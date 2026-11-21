import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.diagnosis.bayesian_schemas import DiagnosticQuestionModel
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.error_detector import FirstErrorDetector
from backend.app.diagnosis.error_schemas import ExpectedStep, QuestionRubric
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.question_selector import ActiveQuestionSelector
from backend.app.diagnosis.reasoning_extractor import MockLLMProvider, ReasoningExtractor
from backend.app.diagnosis.response_interpreter import MockResponseInterpreter
from backend.app.diagnosis.service import DiagnosisService
from backend.app.diagnosis.session_repository import SQLiteSessionRepository
from backend.app.main import app, set_diagnosis_service

DATA_DIR = Path("data")


@pytest.fixture
def test_service():
    cg = ConceptGraph.load_from_json(DATA_DIR / "concepts" / "physics_force_motion.json")
    ml = MisconceptionLibrary.load_from_json(DATA_DIR / "misconceptions" / "physics_force_motion.json", concept_graph=cg)
    qs = ActiveQuestionSelector.load_from_json(DATA_DIR / "misconceptions" / "likelihoods.json")

    mock_llm = MockLLMProvider()
    re = ReasoningExtractor(provider=mock_llm, concept_graph=cg)
    ed = FirstErrorDetector(misconception_library=ml, concept_graph=cg)
    ri = MockResponseInterpreter(
        canned_mappings={
            "truck exerts more force": "supports_hypothesis",
            "car accelerates more because smaller mass": "weakens_hypothesis",
            "equal force": "weakens_hypothesis",
        },
        default_category="neutral_or_inconclusive",
    )
    repo = SQLiteSessionRepository(db_path=":memory:")

    svc = DiagnosisService(
        concept_graph=cg,
        misconception_library=ml,
        question_selector=qs,
        reasoning_extractor=re,
        error_detector=ed,
        response_interpreter=ri,
        session_repository=repo,
    )
    set_diagnosis_service(svc)
    return svc


@pytest.fixture
def client(test_service):
    return TestClient(app)


@pytest.fixture
def sample_rubric_payload():
    return {
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "expected_steps": [
            {
                "step_id": "exp_1",
                "expected_concept_ids": ["mass"],
                "expected_principle": "Identify mass: m = 5 kg",
                "acceptable_reasoning": ["Mass is 5 kg."],
                "acceptable_formulas": [],
                "validation_criteria": {},
            },
            {
                "step_id": "exp_2",
                "expected_concept_ids": ["force", "net_force"],
                "expected_principle": "Subtract opposing forces: F_net = 20 - 10 = 10 N",
                "acceptable_reasoning": ["Net force is 20 - 10 = 10 N."],
                "acceptable_formulas": ["F_net = F1 - F2"],
                "validation_criteria": {},
            },
            {
                "step_id": "exp_3",
                "expected_concept_ids": ["acceleration", "newton_second_law"],
                "expected_principle": "Calculate acceleration: a = F / m = 10 / 5 = 2 m/s^2",
                "acceptable_reasoning": ["Acceleration is 10 / 5 = 2 m/s^2."],
                "acceptable_formulas": ["a = F / m"],
                "validation_criteria": {},
            },
        ],
        "accepted_alternative_methods": [],
        "expected_answer": "2 m/s^2 right",
        "relevant_concept_ids": ["mass", "force", "net_force", "acceleration", "newton_second_law"],
    }


# 1. Successful initial diagnosis
def test_successful_initial_diagnosis(client, sample_rubric_payload, test_service):
    # Configure mock LLM response
    resp_text = "Mass is 5 kg. Net force is 20 + 10 = 30 N. Acceleration is 30 divided by 5, which equals 6 m/s^2."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "Mass is 5 kg.",
                "claim": "Mass is 5 kg",
                "reasoning_type": "factual_claim",
                "concept_ids": ["mass"],
                "formulas": [],
                "evidence_text": "Mass is 5 kg.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "Net force is 20 + 10 = 30 N.",
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": "Net force is 20 + 10 = 30 N.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_3",
                "order": 3,
                "original_text": "Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                "claim": "Acceleration is 30 divided by 5, which equals 6 m/s^2",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["acceleration"],
                "formulas": [],
                "evidence_text": "Acceleration is 30 divided by 5, which equals 6 m/s^2.",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["mass", "net_force", "acceleration"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    payload = {
        "student_id": "student_001",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["mass", "force", "net_force", "acceleration", "newton_second_law"],
    }

    res = client.post("/api/diagnosis/submit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "diagnosis_session_id" in data
    assert data["student_id"] == "student_001"
    assert data["first_error_result"]["first_error_step_id"] == "step_2"
    assert data["first_error_result"]["error_type"] == "direction_or_sign_error"
    assert "step_3" in data["first_error_result"]["downstream_affected_steps"]


# 2. Correct student answer
def test_correct_student_answer(client, sample_rubric_payload, test_service):
    resp_text = "Mass is 5 kg. Net force is 20 - 10 = 10 N. Acceleration is 10 / 5 = 2 m/s^2."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "Mass is 5 kg.",
                "claim": "Mass is 5 kg",
                "reasoning_type": "factual_claim",
                "concept_ids": ["mass"],
                "formulas": [],
                "evidence_text": "Mass is 5 kg.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "Net force is 20 - 10 = 10 N.",
                "claim": "Net force is 10 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": "Net force is 20 - 10 = 10 N.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_3",
                "order": 3,
                "original_text": "Acceleration is 10 / 5 = 2 m/s^2.",
                "claim": "Acceleration is 2 m/s^2",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["acceleration"],
                "formulas": [],
                "evidence_text": "Acceleration is 10 / 5 = 2 m/s^2.",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["mass", "net_force", "acceleration"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 - 10", mock_json)

    payload = {
        "student_id": "student_002",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["mass", "force", "net_force", "acceleration"],
    }

    res = client.post("/api/diagnosis/submit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["first_error_result"]["first_error_step_id"] is None
    assert data["selected_followup_question"] is None
    assert data["diagnostic_status"] == "sufficient_evidence"


# 3. Incorrect reasoning with detectable first error
def test_incorrect_reasoning_detectable_first_error(client, sample_rubric_payload, test_service):
    # Tests that step 2 is marked as the first error
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    payload = {
        "student_id": "student_003",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    }
    res = client.post("/api/diagnosis/submit", json=payload)
    data = res.json()
    assert data["first_error_result"]["first_error_step_id"] == "step_1"
    assert data["first_error_result"]["error_type"] == "direction_or_sign_error"


# 4. Candidate misconception retrieval
def test_candidate_misconception_retrieval(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force", "force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force", "force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    payload = {
        "student_id": "student_004",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force", "force"],
    }
    res = client.post("/api/diagnosis/submit", json=payload)
    data = res.json()
    assert len(data["candidate_misconception_ids"]) > 0


# 5. Follow-up question selection
def test_followup_question_selection(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force", "force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force", "force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    payload = {
        "student_id": "student_005",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg object experiences a 20 N force to the right and a 10 N force to the left. Calculate its acceleration.",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force", "force"],
    }
    res = client.post("/api/diagnosis/submit", json=payload)
    data = res.json()
    followup = data["selected_followup_question"]
    assert followup is not None
    assert "question_id" in followup
    assert "expected_information_gain" in followup


# 6. Follow-up response interpretation
def test_followup_response_interpretation(client, sample_rubric_payload, test_service):
    # Setup initial session
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_006",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]
    followup_qid = sub_res.json()["selected_followup_question"]["question_id"]

    # Submit followup
    f_res = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": followup_qid,
        "student_response": "The car accelerates more because smaller mass under equal force.",
    })
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert f_data["interpreted_evidence"]["response_category"] == "weakens_hypothesis"


# 7. Bayesian posterior update
def test_bayesian_posterior_update(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_007",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]
    followup_qid = sub_res.json()["selected_followup_question"]["question_id"]
    initial_priors = sub_res.json()["posterior_hypothesis_distribution"]

    f_res = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": followup_qid,
        "student_response": "The truck exerts more force because it is heavier.",
    })
    f_data = f_res.json()
    updated_posts = f_data["updated_hypothesis_distribution"]

    # Verify probability distribution updated
    assert updated_posts != initial_priors
    assert pytest.approx(sum(updated_posts.values()), 0.001) == 1.0


# 8. Multiple follow-up rounds
def test_multiple_followup_rounds(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_008",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]
    q1 = sub_res.json()["selected_followup_question"]["question_id"]

    # Round 1
    r1 = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": q1,
        "student_response": "truck exerts more force",
    })
    assert r1.status_code == 200
    assert r1.json()["evidence_history_count"] == 1

    # Round 2
    q2 = r1.json()["next_followup_question"]
    if q2:
        r2 = client.post("/api/diagnosis/followup", json={
            "diagnosis_session_id": session_id,
            "followup_question_id": q2["question_id"],
            "student_response": "equal force",
        })
        assert r2.status_code == 200
        assert r2.json()["evidence_history_count"] == 2


# 9. Duplicate follow-up rejection
def test_duplicate_followup_rejection(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_009",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]
    q1 = sub_res.json()["selected_followup_question"]["question_id"]

    # First submission
    client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": q1,
        "student_response": "truck exerts more force",
    })

    # Duplicate submission
    dup_res = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": q1,
        "student_response": "truck exerts more force again",
    })
    assert dup_res.status_code == 400
    assert "already been answered" in dup_res.json()["detail"]


# 10. Unknown/other hypothesis preservation
def test_unknown_or_other_hypothesis_preservation(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_010",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    data = sub_res.json()
    assert "unknown_or_other" in data["posterior_hypothesis_distribution"]


# 11. Insufficient reasoning
def test_insufficient_reasoning(client, sample_rubric_payload):
    payload = {
        "student_id": "student_011",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": "No",
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    }
    res = client.post("/api/diagnosis/submit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["diagnostic_status"] == "inconclusive"
    assert data["extracted_reasoning"]["extraction_status"] == "insufficient_information"


# 12. Ambiguous response handling in follow-up
def test_ambiguous_response_handling(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_012",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]
    q1 = sub_res.json()["selected_followup_question"]["question_id"]

    f_res = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": session_id,
        "followup_question_id": q1,
        "student_response": "I really do not know what happens maybe both.",
    })
    assert f_res.status_code == 200
    assert f_res.json()["interpreted_evidence"]["response_category"] == "neutral_or_inconclusive"


# 13. No available diagnostic questions
def test_no_available_diagnostic_questions(client, sample_rubric_payload, test_service):
    # Empty question selector catalog
    test_service.question_selector.question_catalog = []

    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_013",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    assert res.status_code == 200
    assert res.json()["selected_followup_question"] is None
    assert res.json()["diagnostic_status"] == "no_available_questions"


# 14. Invalid question or concept ID
def test_invalid_concept_id_handling(client, sample_rubric_payload):
    bad_payload = dict(sample_rubric_payload)
    bad_payload["relevant_concept_ids"] = ["quantum_entanglement"]

    res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_014",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": "Net force is 10 N.",
        "rubric": bad_payload,
        "relevant_concept_ids": ["quantum_entanglement"],
    })
    assert res.status_code == 400
    assert "unknown relevant concept" in res.json()["detail"].lower()


# 15. Unknown session ID
def test_unknown_session_id(client):
    res = client.post("/api/diagnosis/followup", json={
        "diagnosis_session_id": "nonexistent_session_12345",
        "followup_question_id": "DQ_PHY_M009_1",
        "student_response": "Some response",
    })
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# 16. Session persistence and retrieval
def test_session_persistence_and_export(client, sample_rubric_payload, test_service):
    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    sub_res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_016",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    session_id = sub_res.json()["diagnosis_session_id"]

    # Check export endpoint for Member 2
    exp_res = client.get(f"/api/diagnosis/session/{session_id}/export")
    assert exp_res.status_code == 200
    export_data = exp_res.json()
    assert export_data["student_id"] == "student_016"
    assert export_data["session_id"] == session_id
    assert "posterior_hypotheses" in export_data
    assert "prerequisite_concepts_to_review" in export_data


# 17. API validation errors
def test_api_validation_errors(client):
    # Missing required student_id
    res = client.post("/api/diagnosis/submit", json={
        "question_id": "Q1",
        "question_text": "Text",
        "student_response": "Resp",
    })
    assert res.status_code == 422


# 18. Health endpoint
def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["registered_concepts"] == 23
    assert data["registered_misconceptions"] == 24


# 19. Concept endpoint
def test_concept_endpoint(client):
    res = client.get("/api/diagnosis/concepts")
    assert res.status_code == 200
    data = res.json()
    assert data["subject"] == "Physics"
    assert data["total_concepts"] == 23
    assert data["total_prerequisite_edges"] == 30
    assert len(data["concepts"]) == 23


# 20. Unavailable likelihood model fallback
def test_unavailable_likelihood_model_fallback(client, sample_rubric_payload, test_service):
    # Add a question model with no response likelihoods
    uncalibrated_q = DiagnosticQuestionModel(
        question_id="DQ_UNCALIBRATED",
        question_text="Uncalibrated probe?",
        target_hypotheses=["PHY_M008"],
        response_likelihoods={},
        calibration_status="illustrative",
    )
    test_service.question_selector.question_catalog = [uncalibrated_q]

    resp_text = "Net force is 20 + 10 = 30 N."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": resp_text,
                "claim": "Net force is 20 + 10 = 30 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": resp_text,
                "uncertainty_flag": False,
            }
        ],
        "identified_concepts": ["net_force"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    test_service.reasoning_extractor.provider.register_response("Net force is 20 + 10", mock_json)

    res = client.post("/api/diagnosis/submit", json={
        "student_id": "student_020",
        "question_id": "Q_ACCEL_01",
        "question_text": "Test question",
        "student_response": resp_text,
        "rubric": sample_rubric_payload,
        "relevant_concept_ids": ["net_force"],
    })
    assert res.status_code == 200
    data = res.json()
    followup = data["selected_followup_question"]
    assert followup is not None
    assert followup["question_id"] == "DQ_UNCALIBRATED"
    assert followup["expected_information_gain"] == 0.0
    assert "fallback" in followup["selection_rationale"].lower()
