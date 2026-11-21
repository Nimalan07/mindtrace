from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.error_detector import FirstErrorDetector
from backend.app.diagnosis.error_schemas import (
    ExpectedStep,
    FirstErrorResult,
    QuestionRubric,
)
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.reasoning_schemas import (
    ExtractedReasoning,
    ReasoningStep,
)

CONCEPT_PATH = Path("data/concepts/physics_force_motion.json")
MISCONCEPTION_PATH = Path("data/misconceptions/physics_force_motion.json")


@pytest.fixture
def concept_graph():
    return ConceptGraph.load_from_json(CONCEPT_PATH)


@pytest.fixture
def misconception_library(concept_graph):
    return MisconceptionLibrary.load_from_json(
        MISCONCEPTION_PATH,
        concept_graph=concept_graph,
    )


@pytest.fixture
def sample_rubric():
    return QuestionRubric(
        question_id="Q_ACCEL_01",
        question_text="A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        expected_steps=[
            ExpectedStep(
                step_id="exp_1",
                expected_concept_ids=["mass"],
                expected_principle="Identify mass: m = 5 kg",
                acceptable_reasoning=["Mass is 5 kg."],
                acceptable_formulas=[],
            ),
            ExpectedStep(
                step_id="exp_2",
                expected_concept_ids=["force", "net_force"],
                expected_principle="Subtract opposing forces for net force: F_net = 20 - 10 = 10 N right",
                acceptable_reasoning=["Net force is 20 - 10 = 10 N."],
                acceptable_formulas=["F_net = F1 - F2"],
            ),
            ExpectedStep(
                step_id="exp_3",
                expected_concept_ids=["acceleration", "newton_second_law"],
                expected_principle="Calculate acceleration: a = F_net / m = 10 / 5 = 2 m/s^2 right",
                acceptable_reasoning=["Acceleration is 10 / 5 = 2 m/s^2."],
                acceptable_formulas=["a = F_net / m"],
            ),
        ],
        accepted_alternative_methods=["momentum_impulse_method"],
        expected_answer="2 m/s^2 to the right",
        relevant_concept_ids=["mass", "force", "net_force", "acceleration", "newton_second_law"],
    )


# 1. All reasoning steps correct
def test_all_reasoning_steps_correct(sample_rubric, misconception_library, concept_graph):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Mass is 5 kg. Net force is 20 - 10 = 10 N. Acceleration is 10 / 5 = 2 m/s^2.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Mass is 5 kg.",
                claim="Mass is 5 kg",
                reasoning_type="factual_claim",
                concept_ids=["mass"],
                evidence_text="Mass is 5 kg.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="Net force is 20 - 10 = 10 N.",
                claim="Net force is 10 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force"],
                evidence_text="Net force is 20 - 10 = 10 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_3",
                order=3,
                original_text="Acceleration is 10 / 5 = 2 m/s^2.",
                claim="Acceleration is 2 m/s^2",
                reasoning_type="mathematical_operation",
                concept_ids=["acceleration", "newton_second_law"],
                evidence_text="Acceleration is 10 / 5 = 2 m/s^2.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["mass", "net_force", "acceleration", "newton_second_law"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id is None
    assert result.first_error_order is None
    assert result.confidence_level == "high"
    assert all(se.status == "correct" for se in result.step_evaluations)
    assert len(result.candidate_misconception_ids) == 0


# 2. First conceptual error detected
def test_first_conceptual_error_detected(misconception_library, concept_graph):
    rubric = QuestionRubric(
        question_id="Q_COLLISION",
        question_text="A heavy truck collides with a small car. Which vehicle experiences the greater force?",
        expected_steps=[
            ExpectedStep(
                step_id="exp_1",
                expected_concept_ids=["newton_third_law"],
                expected_principle="Third law requires equal and opposite forces",
                acceptable_reasoning=["Forces are equal in magnitude"],
                acceptable_formulas=["F_truck = -F_car"],
            )
        ],
        expected_answer="Both experience forces of equal magnitude.",
        relevant_concept_ids=["mass", "force", "newton_third_law"],
    )

    extracted = ExtractedReasoning(
        question_id="Q_COLLISION",
        original_student_response="The truck experiences greater force because it has more mass.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="The truck experiences greater force because it has more mass.",
                claim="Truck experiences greater force due to more mass",
                reasoning_type="conceptual_assumption",
                concept_ids=["mass", "force", "newton_third_law"],
                evidence_text="The truck experiences greater force because it has more mass.",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["mass", "force", "newton_third_law"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, rubric)

    assert result.first_error_step_id == "step_1"
    assert result.error_type == "conceptual_error"
    assert "PHY_M009" in result.candidate_misconception_ids


# 3. First mathematical error detected
def test_first_mathematical_error_detected(sample_rubric, misconception_library, concept_graph):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Mass is 5 kg. Net force is 20 - 10 = 10 N. Acceleration is 10 / 5 = 4 m/s^2.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Mass is 5 kg.",
                claim="Mass is 5 kg",
                reasoning_type="factual_claim",
                concept_ids=["mass"],
                evidence_text="Mass is 5 kg.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="Net force is 20 - 10 = 10 N.",
                claim="Net force is 10 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force"],
                evidence_text="Net force is 20 - 10 = 10 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_3",
                order=3,
                original_text="Acceleration is 10 / 5 = 4 m/s^2.",
                claim="Acceleration is 10 / 5 = 4",
                reasoning_type="mathematical_operation",
                concept_ids=["acceleration"],
                evidence_text="Acceleration is 10 / 5 = 4 m/s^2.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["mass", "net_force", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_3"
    assert result.error_type == "mathematical_error"
    assert len(result.downstream_affected_steps) == 0


# 4. Formula selection error
def test_formula_selection_error(sample_rubric, misconception_library, concept_graph):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="We find force using F = m * v instead of F = m * a.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="We find force using F = m * v instead of F = m * a.",
                claim="Calculates force using F = m * v",
                reasoning_type="formula_selection",
                concept_ids=["force"],
                formulas=["F = m * v"],
                evidence_text="F = m * v",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["force"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_1"
    assert result.error_type == "formula_selection_error"


# 5. Direction/sign error (Required demonstration test)
def test_direction_or_sign_error(sample_rubric, misconception_library, concept_graph):
    # Requirement 9: Net force is 20 + 10 = 30 N. Acceleration is 30 divided by 5, which equals 6 m/s^2.
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Mass is 5 kg. Net force is 20 + 10 = 30 N. Acceleration is 30 divided by 5, which equals 6 m/s^2.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Mass is 5 kg.",
                claim="Mass is 5 kg",
                reasoning_type="factual_claim",
                concept_ids=["mass"],
                evidence_text="Mass is 5 kg.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="Net force is 20 + 10 = 30 N.",
                claim="Net force is 20 + 10 = 30 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force"],
                evidence_text="Net force is 20 + 10 = 30 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_3",
                order=3,
                original_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                claim="Acceleration is 30 divided by 5, which equals 6 m/s^2",
                reasoning_type="mathematical_operation",
                concept_ids=["acceleration"],
                evidence_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["mass", "net_force", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_2"
    assert result.first_error_order == 2
    assert result.error_type == "direction_or_sign_error"
    assert result.step_evaluations[0].status == "correct"
    assert result.step_evaluations[1].status == "incorrect"
    assert result.step_evaluations[1].is_downstream_error is False


# 6. Logical inference error
def test_logical_inference_error(concept_graph):
    rubric = QuestionRubric(
        question_id="Q_FIRST_LAW",
        question_text="If acceleration is zero, what can be concluded about velocity?",
        expected_steps=[
            ExpectedStep(
                step_id="exp_1",
                expected_concept_ids=["newton_first_law"],
                expected_principle="Zero acceleration implies constant velocity",
                acceptable_reasoning=["Velocity is constant."],
                acceptable_formulas=[],
            )
        ],
        expected_answer="Velocity is constant (not necessarily zero).",
        relevant_concept_ids=["velocity", "acceleration", "newton_first_law"],
    )

    extracted = ExtractedReasoning(
        question_id="Q_FIRST_LAW",
        original_student_response="Because a = 0, therefore velocity is zero.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Because a = 0, therefore velocity is zero.",
                claim="Because a = 0, therefore velocity is zero",
                reasoning_type="inference",
                concept_ids=["velocity", "acceleration"],
                evidence_text="Because a = 0, therefore velocity is zero.",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["velocity", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(concept_graph=concept_graph)
    result = detector.evaluate(extracted, rubric)

    assert result.first_error_step_id == "step_1"
    assert result.error_type == "logical_inference_error"


# 7. Downstream steps identified correctly
def test_downstream_steps_identified_correctly(sample_rubric, misconception_library):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Mass is 5 kg. Net force is 20 + 10 = 30 N. Acceleration is 30 divided by 5, which equals 6 m/s^2.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Mass is 5 kg.",
                claim="Mass is 5 kg",
                reasoning_type="factual_claim",
                concept_ids=["mass"],
                evidence_text="Mass is 5 kg.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="Net force is 20 + 10 = 30 N.",
                claim="Net force is 20 + 10 = 30 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force"],
                evidence_text="Net force is 20 + 10 = 30 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_3",
                order=3,
                original_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                claim="Acceleration is 30 divided by 5, which equals 6 m/s^2",
                reasoning_type="mathematical_operation",
                concept_ids=["acceleration"],
                evidence_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["mass", "net_force", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_2"
    assert "step_3" in result.downstream_affected_steps


# 8. Correct downstream arithmetic not marked as new primary error
def test_correct_downstream_arithmetic_not_marked_as_new_primary_error(sample_rubric, misconception_library):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Net force is 20 + 10 = 30 N. Acceleration is 30 divided by 5, which equals 6 m/s^2.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Net force is 20 + 10 = 30 N.",
                claim="Net force is 20 + 10 = 30 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force"],
                evidence_text="Net force is 20 + 10 = 30 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                claim="Acceleration is 30 divided by 5, which equals 6 m/s^2",
                reasoning_type="mathematical_operation",
                concept_ids=["acceleration"],
                evidence_text="Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["net_force", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library)
    result = detector.evaluate(extracted, sample_rubric)

    step_2_eval = result.step_evaluations[1]
    assert step_2_eval.is_downstream_error is True
    # Crucial: Step 2 must NOT be marked as an independent mathematical_error
    assert step_2_eval.error_type != "mathematical_error"


# 9. Multiple errors with the earliest error selected
def test_multiple_errors_earliest_selected(sample_rubric, misconception_library):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="We find force using F = m * v instead of F = m * a. And 10 / 5 = 4.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="We find force using F = m * v instead of F = m * a.",
                claim="Uses F = m * v",
                reasoning_type="formula_selection",
                concept_ids=["force"],
                formulas=["F = m * v"],
                evidence_text="F = m * v",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="And 10 / 5 = 4.",
                claim="10 / 5 = 4",
                reasoning_type="mathematical_operation",
                concept_ids=["force"],
                evidence_text="10 / 5 = 4",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["force"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library)
    result = detector.evaluate(extracted, sample_rubric)

    # First error must be step_1, not step_2
    assert result.first_error_step_id == "step_1"
    assert result.error_type == "formula_selection_error"


# 10. Ambiguous reasoning returns uncertain
def test_ambiguous_reasoning_returns_uncertain(sample_rubric):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Maybe the net force is 10 N or 30 N I am not sure.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Maybe the net force is 10 N or 30 N I am not sure.",
                claim="Uncertain net force",
                reasoning_type="unknown",
                concept_ids=["net_force"],
                evidence_text="Maybe the net force is 10 N or 30 N I am not sure.",
                uncertainty_flag=True,
            )
        ],
        identified_concepts=["net_force"],
        extraction_status="partial",
        ambiguity_notes=["Student expressed high uncertainty."],
    )

    detector = FirstErrorDetector()
    result = detector.evaluate(extracted, sample_rubric)

    assert result.confidence_level == "uncertain"
    assert result.step_evaluations[0].status == "uncertain"


# 11. Incomplete student reasoning
def test_incomplete_student_reasoning(sample_rubric):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="I think so",
        reasoning_steps=[],
        identified_concepts=[],
        extraction_status="insufficient_information",
        ambiguity_notes=["Too brief."],
    )

    detector = FirstErrorDetector()
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id is None
    assert result.confidence_level == "uncertain"
    assert len(result.uncertainty_notes) > 0


# 12. No misconception candidate found for pure arithmetic error
def test_no_misconception_candidate_found(sample_rubric, misconception_library):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Net force is 10 N. 10 / 5 = 4.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Net force is 10 N.",
                claim="Net force is 10 N",
                reasoning_type="factual_claim",
                concept_ids=["net_force"],
                evidence_text="Net force is 10 N.",
                uncertainty_flag=False,
            ),
            ReasoningStep(
                step_id="step_2",
                order=2,
                original_text="10 / 5 = 4.",
                claim="10 / 5 = 4",
                reasoning_type="mathematical_operation",
                concept_ids=[],
                evidence_text="10 / 5 = 4.",
                uncertainty_flag=False,
            ),
        ],
        identified_concepts=["net_force"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library)
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_2"
    assert result.error_type == "mathematical_error"
    # Arithmetic errors must NOT fabricate misconception candidates
    assert len(result.candidate_misconception_ids) == 0


# 13. Candidate misconception retrieval works
def test_candidate_misconception_retrieval_works(misconception_library, concept_graph):
    rubric = QuestionRubric(
        question_id="Q_THIRD_LAW",
        question_text="Does a truck exert more force than a car in a collision?",
        expected_steps=[
            ExpectedStep(
                step_id="exp_1",
                expected_concept_ids=["newton_third_law"],
                expected_principle="Third Law symmetry",
                acceptable_reasoning=["Forces are equal and opposite."],
                acceptable_formulas=[],
            )
        ],
        expected_answer="Equal force magnitudes.",
        relevant_concept_ids=["mass", "force", "newton_third_law"],
    )

    extracted = ExtractedReasoning(
        question_id="Q_THIRD_LAW",
        original_student_response="The truck experiences greater force because it has more mass.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="The truck experiences greater force because it has more mass.",
                claim="Truck has greater force due to more mass",
                reasoning_type="conceptual_assumption",
                concept_ids=["mass", "force", "newton_third_law"],
                evidence_text="The truck experiences greater force because it has more mass.",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["mass", "force", "newton_third_law"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library, concept_graph=concept_graph)
    result = detector.evaluate(extracted, rubric)

    assert "PHY_M009" in result.candidate_misconception_ids


# 14. Multiple candidate misconceptions returned without confirmation
def test_multiple_candidate_misconceptions_returned_without_confirmation(sample_rubric, misconception_library):
    # An error on net force and vector direction
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Net force is 20 + 10 = 30 N.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Net force is 20 + 10 = 30 N.",
                claim="Net force is 20 + 10 = 30 N",
                reasoning_type="mathematical_operation",
                concept_ids=["net_force", "force"],
                evidence_text="Net force is 20 + 10 = 30 N.",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["net_force", "force"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector(misconception_library=misconception_library)
    result = detector.evaluate(extracted, sample_rubric)

    # Returns candidates (like PHY_M008, PHY_M005, etc.) but does NOT confirm any
    assert len(result.candidate_misconception_ids) > 1
    # Check that they remain hypotheses (IDs list only, no posterior probabilities assigned)
    assert isinstance(result.candidate_misconception_ids, list)


# 15. Alternative valid reasoning method accepted
def test_alternative_valid_reasoning_method_accepted():
    rubric = QuestionRubric(
        question_id="Q_ENERGY_ALT",
        question_text="Find the final speed of the object.",
        expected_steps=[
            ExpectedStep(
                step_id="exp_1",
                expected_concept_ids=["kinematics"],
                expected_principle="Standard kinematic formula v^2 = u^2 + 2as",
                acceptable_reasoning=["Kinematics formula"],
                acceptable_formulas=["v^2 = u^2 + 2as"],
            )
        ],
        accepted_alternative_methods=["work_energy_method"],
        expected_answer="v = 10 m/s",
        relevant_concept_ids=["work", "kinetic_energy"],
    )

    extracted = ExtractedReasoning(
        question_id="Q_ENERGY_ALT",
        original_student_response="Solved using work_energy_method: W = delta KE.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Solved using work_energy_method: W = delta KE.",
                claim="Applies work_energy_method",
                reasoning_type="formula_selection",
                concept_ids=["work", "kinetic_energy"],
                formulas=["W = delta KE"],
                evidence_text="work_energy_method",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["work", "kinetic_energy"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector()
    result = detector.evaluate(extracted, rubric)

    assert result.step_evaluations[0].status == "correct"
    assert "alternative method" in result.step_evaluations[0].explanation


# 16. Missing or invalid rubric data rejected
def test_missing_or_invalid_rubric_data_rejected():
    with pytest.raises(ValidationError):
        QuestionRubric(
            question_id="Q_BAD",
            question_text="",  # empty
            expected_steps=[],  # empty
            expected_answer="answer",
            relevant_concept_ids=[],
        )


# 17. Concept references validated
def test_concept_references_validated(concept_graph):
    bad_rubric = QuestionRubric(
        question_id="Q_INVALID_CONCEPTS",
        question_text="Calculate warp speed.",
        expected_steps=[
            ExpectedStep(
                step_id="step_1",
                expected_concept_ids=["warp_drive"],  # unknown in concept graph
                expected_principle="Warp mechanics",
            )
        ],
        expected_answer="Warp 9",
        relevant_concept_ids=["warp_drive"],
    )

    detector = FirstErrorDetector(concept_graph=concept_graph)
    with pytest.raises(InvalidConceptReferenceError) as exc_info:
        detector.validate_rubric(bad_rubric)
    assert "warp_drive" in str(exc_info.value)


# 18. Missing prerequisite represented appropriately
def test_missing_prerequisite_represented_appropriately(sample_rubric):
    extracted = ExtractedReasoning(
        question_id="Q_ACCEL_01",
        original_student_response="Velocity is acceleration so we just use velocity directly.",
        reasoning_steps=[
            ReasoningStep(
                step_id="step_1",
                order=1,
                original_text="Velocity is acceleration so we just use velocity directly.",
                claim="Velocity is acceleration",
                reasoning_type="conceptual_assumption",
                concept_ids=["velocity", "acceleration"],
                evidence_text="Velocity is acceleration",
                uncertainty_flag=False,
            )
        ],
        identified_concepts=["velocity", "acceleration"],
        extraction_status="complete",
    )

    detector = FirstErrorDetector()
    result = detector.evaluate(extracted, sample_rubric)

    assert result.first_error_step_id == "step_1"
    assert result.error_type == "missing_prerequisite"
