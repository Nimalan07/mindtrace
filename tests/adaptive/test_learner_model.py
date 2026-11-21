import pytest

from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


@pytest.fixture
def learner() -> LearnerModel:
    return LearnerModel()


def test_learner_model_initialization(learner: LearnerModel):
    m = learner.get_concept_mastery("student_1", "net_force")
    assert m == 0.25  # default p_l0


def test_learner_model_assessment_update(learner: LearnerModel):
    res = learner.update_from_assessment("student_1", "net_force", is_correct=True, question_id="Q_01")
    assert res.updated_mastery > 0.25

    profile = learner.get_or_create_profile("student_1")
    assert profile.total_assessments == 1
    assert profile.total_correct == 1
    assert "net_force" in profile.concept_masteries
    assert len(profile.concept_masteries["net_force"].history) == 1


def test_learner_model_consume_diagnosis_export(learner: LearnerModel):
    export = Member2DiagnosisExport(
        student_id="student_42",
        session_id="diag_session_abc",
        question_id="Q_NETF_01",
        relevant_concept_ids=["net_force", "force"],
        first_error_concept_id="net_force",
        first_error_step_order=2,
        identified_error_category="direction_or_sign_error",
        candidate_misconception_ids=["PHY_M008"],
        posterior_hypotheses={"PHY_M008": 0.85, "unknown_or_other": 0.15},
        diagnostic_status="sufficient_evidence",
        prerequisite_concepts_to_review=["force"],
        evidence_confidence=0.90,
    )

    updates = learner.update_from_diagnosis_export(export)
    assert "net_force" in updates
    bkt_res = updates["net_force"]
    assert bkt_res.is_correct is False
    assert bkt_res.concept_id == "net_force"

    # Verify history recorded
    profile = learner.get_or_create_profile("student_42")
    history = profile.concept_masteries["net_force"].history
    assert len(history) == 1
    assert history[0]["source"] == "diagnosis_export"
    assert history[0]["session_id"] == "diag_session_abc"
