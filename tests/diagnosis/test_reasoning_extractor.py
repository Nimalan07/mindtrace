import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.reasoning_extractor import (
    FailingLLMProvider,
    MockLLMProvider,
    ReasoningExtractor,
)
from backend.app.diagnosis.reasoning_schemas import (
    ExtractedReasoning,
    ReasoningStep,
)

CONCEPT_PATH = Path("data/concepts/physics_force_motion.json")


@pytest.fixture
def concept_graph():
    return ConceptGraph.load_from_json(CONCEPT_PATH)


# 1. Successful structured extraction
def test_successful_structured_extraction(concept_graph):
    question = "A heavy truck collides with a small car. Which vehicle experiences the greater force?"
    student_response = "The truck experiences greater force because it has more mass."

    mock_output = json.dumps({
        "question_id": "Q001",
        "original_student_response": student_response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "The truck experiences greater force",
                "claim": "Truck experiences greater force than car",
                "reasoning_type": "conclusion",
                "concept_ids": ["force"],
                "formulas": [],
                "inference": "Direct conclusion",
                "evidence_text": "The truck experiences greater force",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "because it has more mass",
                "claim": "Heavier objects exert or experience greater force",
                "reasoning_type": "conceptual_assumption",
                "concept_ids": ["mass"],
                "formulas": [],
                "inference": "Supports step 1",
                "evidence_text": "because it has more mass",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["force", "mass"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider, concept_graph=concept_graph)

    extracted = extractor.extract_reasoning(question, student_response, question_id="Q001")

    assert extracted.extraction_status == "complete"
    assert len(extracted.reasoning_steps) == 2
    assert extracted.identified_concepts == ["force", "mass"]
    assert extracted.reasoning_steps[0].claim == "Truck experiences greater force than car"
    assert extracted.reasoning_steps[1].concept_ids == ["mass"]


# 2. Multiple ordered reasoning steps
def test_multiple_ordered_reasoning_steps():
    response = "First a = 2 m/s^2. Then F = m * a. So F = 20 N."
    mock_output = json.dumps({
        "question_id": "Q002",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "First a = 2 m/s^2.",
                "claim": "Acceleration is 2 m/s^2",
                "reasoning_type": "factual_claim",
                "concept_ids": ["acceleration"],
                "formulas": [],
                "evidence_text": "First a = 2 m/s^2.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "Then F = m * a.",
                "claim": "Applies Newton's second law",
                "reasoning_type": "formula_selection",
                "concept_ids": ["newton_second_law"],
                "formulas": ["F = m * a"],
                "evidence_text": "Then F = m * a.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_3",
                "order": 3,
                "original_text": "So F = 20 N.",
                "claim": "Calculates resultant force as 20 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["force"],
                "formulas": ["20 = 10 * 2"],
                "evidence_text": "So F = 20 N.",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["acceleration", "newton_second_law", "force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider)
    extracted = extractor.extract_reasoning("Calculate force", response, question_id="Q002")

    assert [s.order for s in extracted.reasoning_steps] == [1, 2, 3]
    assert extracted.reasoning_steps[1].reasoning_type == "formula_selection"


# 3. Formula identification
def test_formula_identification():
    response = "We use KE = 1/2 m v^2 to find energy."
    mock_output = json.dumps({
        "question_id": "Q003",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "We use KE = 1/2 m v^2 to find energy.",
                "claim": "Uses kinetic energy formula",
                "reasoning_type": "formula_selection",
                "concept_ids": ["kinetic_energy"],
                "formulas": ["KE = 1/2 m v^2"],
                "evidence_text": "KE = 1/2 m v^2",
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["kinetic_energy"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider)
    extracted = extractor.extract_reasoning("What formula applies?", response)

    assert "KE = 1/2 m v^2" in extracted.reasoning_steps[0].formulas


# 4. Concept identification
def test_concept_identification(concept_graph):
    response = "Inertia resists the acceleration caused by net force."
    mock_output = json.dumps({
        "question_id": "Q004",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": response,
                "claim": "Inertia opposes acceleration under net force",
                "reasoning_type": "conceptual_assumption",
                "concept_ids": ["inertia", "acceleration", "net_force"],
                "formulas": [],
                "evidence_text": response,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["inertia", "acceleration", "net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider, concept_graph=concept_graph)
    extracted = extractor.extract_reasoning("Explain inertia", response)

    assert set(extracted.identified_concepts) == {"inertia", "acceleration", "net_force"}


# 5. Mathematical-operation extraction
def test_mathematical_operation_extraction():
    response = "W = 10 N * 5 m = 50 J of work done."
    mock_output = json.dumps({
        "question_id": "Q005",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": response,
                "claim": "Calculates work as 50 J",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["work"],
                "formulas": ["W = F * d", "10 * 5 = 50"],
                "evidence_text": "W = 10 N * 5 m = 50 J",
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["work"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider)
    extracted = extractor.extract_reasoning("Compute work", response)

    assert extracted.reasoning_steps[0].reasoning_type == "mathematical_operation"
    assert "10 * 5 = 50" in extracted.reasoning_steps[0].formulas


# 6. Exact evidence-text validation (traceability)
def test_exact_evidence_text_validation():
    # If evidence_text is fabricated and does not exist in response, validation must fail
    with pytest.raises(ValidationError) as exc_info:
        ExtractedReasoning(
            question_id="Q006",
            original_student_response="The ball stopped quickly.",
            reasoning_steps=[
                ReasoningStep(
                    step_id="step_1",
                    order=1,
                    original_text="The ball stopped quickly.",
                    claim="Ball stopped",
                    reasoning_type="conclusion",
                    concept_ids=["velocity"],
                    formulas=[],
                    evidence_text="Fabricated text not in response",
                    uncertainty_flag=False,
                )
            ],
            identified_concepts=["velocity"],
            extraction_status="complete",
        )
    assert "cannot be traced to the original student response" in str(exc_info.value)


# 7. Empty student response
def test_empty_student_response():
    provider = MockLLMProvider()
    extractor = ReasoningExtractor(provider=provider)

    extracted_empty = extractor.extract_reasoning("Any question", "")
    assert extracted_empty.extraction_status == "insufficient_information"
    assert len(extracted_empty.reasoning_steps) == 0

    extracted_whitespace = extractor.extract_reasoning("Any question", "   ")
    assert extracted_whitespace.extraction_status == "insufficient_information"
    assert len(extracted_whitespace.reasoning_steps) == 0


# 8. Insufficient reasoning
def test_insufficient_reasoning():
    response = "No"
    provider = MockLLMProvider()
    extractor = ReasoningExtractor(provider=provider)

    extracted = extractor.extract_reasoning("Does force cause velocity?", response)
    assert extracted.extraction_status == "insufficient_information"
    assert len(extracted.reasoning_steps) == 0


# 9. Ambiguous explanation
def test_ambiguous_explanation():
    response = "Maybe the car has more force or speed I think."
    mock_output = json.dumps({
        "question_id": "Q009",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": response,
                "claim": "Uncertain whether force or speed is greater",
                "reasoning_type": "unknown",
                "concept_ids": ["force", "speed"],
                "formulas": [],
                "evidence_text": "Maybe the car has more force or speed I think.",
                "uncertainty_flag": True,
            }
        ],
        "identified_concepts": ["force", "speed"],
        "extraction_status": "partial",
        "ambiguity_notes": ["Student expressed high uncertainty ('maybe', 'I think')."],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider)
    extracted = extractor.extract_reasoning("Compare vehicles", response)

    assert extracted.extraction_status == "partial"
    assert extracted.reasoning_steps[0].uncertainty_flag is True
    assert len(extracted.ambiguity_notes) > 0


# 10. Invalid concept references against ConceptGraph
def test_invalid_concept_references(concept_graph):
    response = "The particle has quantum spin."
    mock_output = json.dumps({
        "question_id": "Q010",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": response,
                "claim": "Has quantum spin",
                "reasoning_type": "factual_claim",
                "concept_ids": ["quantum_spin"],
                "formulas": [],
                "evidence_text": response,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["quantum_spin"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider, concept_graph=concept_graph)

    with pytest.raises(InvalidConceptReferenceError) as exc_info:
        extractor.extract_reasoning("State property", response, strict_concepts=True)
    assert "quantum_spin" in str(exc_info.value)


# 11. Malformed JSON handling
def test_malformed_json():
    response = "The truck has more mass so it hits harder."
    provider = MockLLMProvider(default_response="Not valid JSON {{{")
    extractor = ReasoningExtractor(provider=provider)

    extracted = extractor.extract_reasoning("Which hits harder?", response)
    assert extracted.extraction_status == "insufficient_information"
    assert any("Malformed JSON" in note for note in extracted.ambiguity_notes)


# 12. Missing required fields in LLM response
def test_missing_required_fields():
    response = "Friction opposes motion."
    # Missing reasoning_steps list
    provider = MockLLMProvider(default_response=json.dumps({
        "question_id": "Q012",
        "identified_concepts": ["friction"],
        "extraction_status": "complete",
    }))
    extractor = ReasoningExtractor(provider=provider)

    extracted = extractor.extract_reasoning("What does friction do?", response)
    assert extracted.extraction_status == "insufficient_information"
    assert any("Validation error" in note for note in extracted.ambiguity_notes)


# 13. Duplicate step IDs
def test_duplicate_step_ids():
    response = "First A then B."
    with pytest.raises(ValidationError) as exc_info:
        ExtractedReasoning(
            question_id="Q013",
            original_student_response=response,
            reasoning_steps=[
                ReasoningStep(
                    step_id="step_1",
                    order=1,
                    original_text="First A",
                    claim="Claim A",
                    reasoning_type="factual_claim",
                    concept_ids=[],
                    evidence_text="First A",
                    uncertainty_flag=False,
                ),
                ReasoningStep(
                    step_id="step_1",  # duplicate ID
                    order=2,
                    original_text="then B.",
                    claim="Claim B",
                    reasoning_type="conclusion",
                    concept_ids=[],
                    evidence_text="then B.",
                    uncertainty_flag=False,
                ),
            ],
            identified_concepts=[],
            extraction_status="complete",
        )
    assert "Duplicate step IDs" in str(exc_info.value)


# 14. Invalid step ordering
def test_invalid_step_ordering():
    response = "Step one and step two."
    with pytest.raises(ValidationError) as exc_info:
        ExtractedReasoning(
            question_id="Q014",
            original_student_response=response,
            reasoning_steps=[
                ReasoningStep(
                    step_id="step_1",
                    order=2,  # starts with 2 instead of 1
                    original_text="Step one",
                    claim="Claim 1",
                    reasoning_type="factual_claim",
                    concept_ids=[],
                    evidence_text="Step one",
                    uncertainty_flag=False,
                )
            ],
            identified_concepts=[],
            extraction_status="complete",
        )
    assert "Reasoning steps order must be sequential starting at 1" in str(exc_info.value)


# 15. LLM provider failure handling
def test_llm_provider_failure():
    response = "The truck has more mass."
    provider = FailingLLMProvider("API service unavailable")
    extractor = ReasoningExtractor(provider=provider)

    extracted = extractor.extract_reasoning("Collision question", response)
    assert extracted.extraction_status == "insufficient_information"
    assert any("API service unavailable" in note for note in extracted.ambiguity_notes)


# 16. Partial extraction
def test_partial_extraction():
    response = "The car experiences greater force because it accelerates more."
    mock_output = json.dumps({
        "question_id": "Q016",
        "original_student_response": response,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "The car experiences greater force",
                "claim": "Car experiences greater force",
                "reasoning_type": "conclusion",
                "concept_ids": ["force"],
                "formulas": [],
                "evidence_text": "The car experiences greater force",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "because it accelerates more.",
                "claim": "Higher acceleration implies greater interaction force",
                "reasoning_type": "conceptual_assumption",
                "concept_ids": ["acceleration"],
                "formulas": [],
                "evidence_text": "because it accelerates more.",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["force", "acceleration"],
        "extraction_status": "partial",
        "ambiguity_notes": ["Incomplete dynamic rationale: omitted mass and Third Law interaction symmetry."],
    })

    provider = MockLLMProvider(default_response=mock_output)
    extractor = ReasoningExtractor(provider=provider)
    extracted = extractor.extract_reasoning("Collision question", response)

    assert extracted.extraction_status == "partial"
    assert "acceleration" in extracted.identified_concepts
    assert extracted.reasoning_steps[1].claim == "Higher acceleration implies greater interaction force"
