import json
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app


@pytest.fixture
def client():
    from backend.app.main import set_diagnosis_service, set_adaptive_service
    from backend.app.diagnosis.service import DiagnosisService
    from backend.app.adaptive_learning.adaptive_service import AdaptiveLearningService

    # Ensure clean default service instances for full E2E journey
    set_diagnosis_service(DiagnosisService.create_default())
    set_adaptive_service(AdaptiveLearningService.create_default())
    return TestClient(app)


def test_full_15_stage_end_to_end_journey(client):
    """
    Validates Phase 6 complete end-to-end student and teacher learning journey.
    Stages 1 to 15 tested sequentially with strict ID, session, and data consistency.
    """
    student_id = "student_e2e_validation_01"

    # Stage 1: Student opens dashboard
    dash_resp = client.get(f"/api/analytics/student/{student_id}")
    assert dash_resp.status_code == 200
    initial_dash = dash_resp.json()
    assert initial_dash["student_id"] == student_id
    assert len(initial_dash["concept_mastery_breakdown"]) == 23

    # Stage 2: Student selects a Physics concept & task
    concepts_resp = client.get("/api/diagnosis/concepts")
    assert concepts_resp.status_code == 200
    concepts_data = concepts_resp.json()
    assert concepts_data["total_concepts"] == 23

    task_resp = client.get("/api/diagnosis/questions/net_force")
    assert task_resp.status_code == 200
    task_data = task_resp.json()
    assert task_data["concept_id"] == "net_force"
    assert "rubric" in task_data

    # Stage 3: Student submits an answer and reasoning (with intentional direction error)
    student_response = (
        "30 N to the right + 10 N to the left = 40 N total force. "
        "Then acceleration = 40 / 5 = 8 m/s²."
    )
    submit_payload = {
        "student_id": student_id,
        "question_id": task_data["question_id"],
        "question_text": task_data["question_text"],
        "student_response": student_response,
        "rubric": task_data["rubric"],
        "relevant_concept_ids": task_data["relevant_concept_ids"],
    }
    diag_submit_resp = client.post("/api/diagnosis/submit", json=submit_payload)
    assert diag_submit_resp.status_code == 200
    diag_result = diag_submit_resp.json()

    session_id = diag_result["diagnosis_session_id"]
    assert session_id.startswith("diag_")

    # Stage 4: Diagnosis engine extracts reasoning
    extracted = diag_result["extracted_reasoning"]
    assert len(extracted["reasoning_steps"]) >= 1

    # Stage 5: First-error detector identifies the earliest reasoning failure
    first_error = diag_result["first_error_result"]
    assert first_error["first_error_step_id"] is not None

    # Stage 6: Bayesian engine selects a diagnostic follow-up probe
    followup_q = diag_result["selected_followup_question"]
    assert followup_q is not None
    assert followup_q["question_id"] is not None

    # Stage 7: Student submits the follow-up response
    followup_payload = {
        "diagnosis_session_id": session_id,
        "followup_question_id": followup_q["question_id"],
        "student_response": "I just added the forces because force is force, 30 + 10 = 40.",
    }
    followup_resp = client.post("/api/diagnosis/followup", json=followup_payload)
    assert followup_resp.status_code == 200
    followup_data = followup_resp.json()

    # Stage 8: Diagnosis engine updates hypothesis beliefs
    posterior = followup_data["updated_hypothesis_distribution"]
    assert len(posterior) >= 2
    assert "unknown_or_other" in posterior

    # Stage 8b: Export Member 2 contract
    export_resp = client.get(f"/api/diagnosis/session/{session_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["student_id"] == student_id
    assert export_data["session_id"] == session_id

    # Stage 9: Adaptive engine recommends an appropriate learning question
    next_q_resp = client.post(
        "/api/adaptive/question/next",
        json={
            "student_id": student_id,
            "target_concept_id": "net_force",
            "allow_prerequisite_diversion": True,
        },
    )
    assert next_q_resp.status_code == 200
    next_q_data = next_q_resp.json()
    assert next_q_data["question"] is not None
    q_id = next_q_data["question"]["id"]

    # Stage 10: Student submits practice answer
    correct_ans = next_q_data["question"]["correct_answer"]
    ans_resp = client.post(
        "/api/adaptive/assessment/submit",
        json={
            "student_id": student_id,
            "question_id": q_id,
            "student_answer": correct_ans,
            "time_spent_seconds": 25.0,
        },
    )
    assert ans_resp.status_code == 200
    eval_data = ans_resp.json()
    assert eval_data["is_correct"] is True

    # Stage 11: BKT updates concept mastery
    assert eval_data["updated_mastery"] > eval_data["prior_mastery"]

    # Stage 12: Intervention engine recommends remediation when needed
    int_resp = client.get(f"/api/adaptive/intervention/{student_id}/net_force")
    assert int_resp.status_code == 200
    plan = int_resp.json()
    assert plan["student_id"] == student_id
    assert len(plan["stages"]) >= 2

    # Stage 13: Spaced repetition schedules revision
    sr_due_resp = client.get(f"/api/adaptive/spaced-repetition/due/{student_id}")
    assert sr_due_resp.status_code == 200

    # Record a spaced review
    review_resp = client.post(
        "/api/adaptive/spaced-repetition/review",
        json={
            "student_id": student_id,
            "concept_id": "net_force",
            "quality_score": 4,
        },
    )
    assert review_resp.status_code == 200
    card_data = review_resp.json()
    assert card_data["concept_id"] == "net_force"
    assert card_data["repetition_count"] >= 1

    # Stage 14: Student dashboard reflects updated analytics
    updated_dash_resp = client.get(f"/api/analytics/student/{student_id}")
    assert updated_dash_resp.status_code == 200
    updated_dash = updated_dash_resp.json()
    assert updated_dash["total_assessments"] >= 1
    assert updated_dash["total_correct"] >= 1

    # Stage 15: Teacher dashboard reflects cohort analytics
    teacher_resp = client.get("/api/analytics/teacher")
    assert teacher_resp.status_code == 200
    teacher_data = teacher_resp.json()
    assert teacher_data["total_students"] >= 1
    assert len(teacher_data["concept_heatmaps"]) == 23
    assert len(teacher_data["actionable_teaching_insights"]) >= 1

    print("\n>>> FULL 15-STAGE END-TO-END WORKFLOW SUCCEEDED CLEANLY! <<<")
