import json
from fastapi.testclient import TestClient
import pytest

from backend.app.adaptive_learning.adaptive_service import AdaptiveLearningService
from backend.app.diagnosis.reasoning_extractor import MockLLMProvider
from backend.app.diagnosis.service import DiagnosisService
from backend.app.main import app, set_adaptive_service, set_diagnosis_service


@pytest.fixture
def client_and_services():
    diag_service = DiagnosisService.create_default(db_path=":memory:")
    adapt_service = AdaptiveLearningService.create_default(db_path=":memory:")

    set_diagnosis_service(diag_service)
    set_adaptive_service(adapt_service)

    return TestClient(app), diag_service, adapt_service


def test_health_check_unified(client_and_services):
    client, _, _ = client_and_services
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mindtrace-unified-platform"
    assert data["registered_concepts"] == 23
    assert data["registered_misconceptions"] == 24
    assert data["question_bank_size"] >= 30


def test_full_member1_member2_end_to_end_flow(client_and_services):
    client, diag_service, _ = client_and_services

    # Configure mock LLM response for student reasoning extraction
    resp_text = "First, the total force is 30 + 10 = 40 N. Then acceleration = 40 / 5 = 8 m/s²."
    mock_json = json.dumps({
        "question_id": "Q_ACCEL_01",
        "original_student_response": resp_text,
        "reasoning_steps": [
            {
                "step_id": "step_1",
                "order": 1,
                "original_text": "First, the total force is 30 + 10 = 40 N.",
                "claim": "Net force is 30 + 10 = 40 N",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["net_force"],
                "formulas": [],
                "evidence_text": "First, the total force is 30 + 10 = 40 N.",
                "uncertainty_flag": False,
            },
            {
                "step_id": "step_2",
                "order": 2,
                "original_text": "Then acceleration = 40 / 5 = 8 m/s².",
                "claim": "Acceleration is 40 / 5 = 8 m/s²",
                "reasoning_type": "mathematical_operation",
                "concept_ids": ["acceleration"],
                "formulas": [],
                "evidence_text": "Then acceleration = 40 / 5 = 8 m/s².",
                "uncertainty_flag": False,
            },
        ],
        "identified_concepts": ["net_force", "acceleration"],
        "extraction_status": "complete",
        "ambiguity_notes": [],
    })
    diag_service.reasoning_extractor.provider.register_response("30 + 10 = 40", mock_json)

    # 1. Member 1: Submit diagnostic reasoning
    submit_payload = {
        "student_id": "student_integration_01",
        "question_id": "Q_ACCEL_01",
        "question_text": "A 5 kg block has a 30 N force to the right and a 10 N force to the left. What is its acceleration?",
        "student_response": resp_text,
        "relevant_concept_ids": ["net_force", "acceleration", "newton_second_law"],
        "rubric": {
            "question_id": "Q_ACCEL_01",
            "question_text": "A 5 kg block has a 30 N force to the right and a 10 N force to the left. What is its acceleration?",
            "expected_steps": [
                {
                    "step_id": "exp_1",
                    "expected_concept_ids": ["mass"],
                    "expected_principle": "Identify mass",
                    "acceptable_reasoning": ["Mass is 5 kg"],
                    "acceptable_formulas": [],
                    "validation_criteria": {},
                },
                {
                    "step_id": "exp_2",
                    "expected_concept_ids": ["force", "net_force"],
                    "expected_principle": "Subtract opposing forces: F_net = 30 - 10 = 20 N",
                    "acceptable_reasoning": ["Net force is 30 - 10 = 20 N."],
                    "acceptable_formulas": ["F_net = F1 - F2"],
                    "validation_criteria": {},
                },
                {
                    "step_id": "exp_3",
                    "expected_concept_ids": ["acceleration", "newton_second_law"],
                    "expected_principle": "Calculate acceleration: a = F / m = 20 / 5 = 4 m/s²",
                    "acceptable_reasoning": ["Acceleration is 20 / 5 = 4 m/s²."],
                    "acceptable_formulas": ["a = F / m"],
                    "validation_criteria": {},
                },
            ],
            "accepted_alternative_methods": [],
            "expected_answer": "4 m/s²",
            "relevant_concept_ids": ["net_force", "acceleration", "newton_second_law"],
        },
    }

    diag_resp = client.post("/api/diagnosis/submit", json=submit_payload)
    assert diag_resp.status_code == 200
    diag_data = diag_resp.json()
    session_id = diag_data["diagnosis_session_id"]
    assert session_id.startswith("diag_")
    assert diag_data["first_error_result"]["first_error_step_id"] is not None
    assert "PHY_M008" in diag_data["candidate_misconception_ids"]

    # 2. Member 1: Followup question response
    followup_q = diag_data["selected_followup_question"]
    if followup_q:
        followup_payload = {
            "diagnosis_session_id": session_id,
            "followup_question_id": followup_q["question_id"],
            "student_response": "I just added the forces because force is force, 30 + 10 = 40.",
        }
        f_resp = client.post("/api/diagnosis/followup", json=followup_payload)
        assert f_resp.status_code == 200

    # 3. Export Member 2 diagnosis contract
    export_resp = client.get(f"/api/diagnosis/session/{session_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["student_id"] == "student_integration_01"
    assert export_data["first_error_concept_id"] == "net_force"
    assert export_data["evidence_confidence"] > 0

    # 4. Member 2: Generate personalized intervention directly from session
    int_resp = client.post(f"/api/adaptive/intervention/session/{session_id}")
    assert int_resp.status_code == 200
    plan = int_resp.json()
    assert plan["student_id"] == "student_integration_01"
    assert plan["target_concept_id"] == "net_force"
    assert len(plan["stages"]) >= 3
    assert len(plan["actionable_summary"]) > 0

    # 5. Member 2: Request next adaptive question for this student
    next_q_resp = client.post(
        "/api/adaptive/question/next",
        json={
            "student_id": "student_integration_01",
            "target_concept_id": "net_force",
            "exclude_question_ids": ["Q_ACCEL_01"],
        },
    )
    assert next_q_resp.status_code == 200
    next_q = next_q_resp.json()
    assert next_q["question"] is not None
    recommended_qid = next_q["question"]["id"]

    # 6. Member 2: Student attempts the adaptive question
    ans_payload = {
        "student_id": "student_integration_01",
        "question_id": recommended_qid,
        "student_answer": next_q["question"]["correct_answer"],
        "time_spent_seconds": 35.0,
    }
    eval_resp = client.post("/api/adaptive/assessment/submit", json=ans_payload)
    assert eval_resp.status_code == 200
    evaluation = eval_resp.json()
    assert evaluation["is_correct"] is True
    assert evaluation["updated_mastery"] > evaluation["prior_mastery"]

    # 7. Member 2: Check spaced repetition schedule
    sr_resp = client.get("/api/adaptive/spaced-repetition/due/student_integration_01")
    assert sr_resp.status_code == 200

    # Record a review
    review_resp = client.post(
        "/api/adaptive/spaced-repetition/review",
        json={
            "student_id": "student_integration_01",
            "concept_id": "net_force",
            "quality_score": 5,
        },
    )
    assert review_resp.status_code == 200
    card = review_resp.json()
    assert card["repetition_count"] >= 1

    # 8. Member 2: Inspect Student Dashboard
    stud_resp = client.get("/api/analytics/student/student_integration_01")
    assert stud_resp.status_code == 200
    dash = stud_resp.json()
    assert dash["student_id"] == "student_integration_01"
    assert dash["total_assessments"] >= 1
    assert len(dash["concept_mastery_breakdown"]) == 23

    # 9. Member 2: Inspect Teacher Dashboard
    teach_resp = client.get("/api/analytics/teacher")
    assert teach_resp.status_code == 200
    t_dash = teach_resp.json()
    assert t_dash["total_students"] >= 1
    assert len(t_dash["concept_heatmaps"]) == 23
    assert len(t_dash["actionable_teaching_insights"]) >= 1
