import pytest

from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionEngine
from backend.app.dashboard.dashboard_schemas import MasteryStatus
from backend.app.dashboard.student_analytics import StudentAnalyticsService
from backend.app.dashboard.teacher_analytics import TeacherAnalyticsService
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


@pytest.fixture
def test_setup():
    cg = ConceptGraph.load_from_json("data/concepts/physics_force_motion.json")
    ml = MisconceptionLibrary.load_from_json("data/misconceptions/physics_force_motion.json", concept_graph=cg)
    learner = LearnerModel()
    sr = SpacedRepetitionEngine()
    return cg, ml, learner, sr


def test_student_dashboard_metrics(test_setup):
    cg, ml, learner, sr = test_setup
    svc = StudentAnalyticsService(learner, cg, sr)

    # Student 1 answers some questions
    learner.update_from_assessment("student_alice", "velocity", is_correct=True, question_id="Q_V1")
    learner.update_from_assessment("student_alice", "velocity", is_correct=True, question_id="Q_V2")
    learner.update_from_assessment("student_alice", "net_force", is_correct=False, question_id="Q_NF1")

    dash = svc.get_student_dashboard("student_alice")
    assert dash.student_id == "student_alice"
    assert dash.total_assessments == 3
    assert dash.total_correct == 2
    assert dash.accuracy_rate == round(2 / 3, 4)
    assert len(dash.concept_mastery_breakdown) == 23  # all 23 concepts tracked
    assert dash.mastery_counts["needs_support"] >= 1


def test_teacher_dashboard_analytics(test_setup):
    cg, ml, learner, sr = test_setup
    teacher_svc = TeacherAnalyticsService(learner, cg, ml)

    # Empty class
    empty_res = teacher_svc.get_teacher_dashboard()
    assert empty_res.total_students == 0

    # Populate 2 students
    # Student 1 does well
    learner.update_from_assessment("s1", "velocity", is_correct=True, question_id="Q1")
    learner.update_from_assessment("s1", "force", is_correct=True, question_id="Q2")

    # Student 2 has diagnosed misconception PHY_M008
    export = Member2DiagnosisExport(
        student_id="s2",
        session_id="session_s2",
        question_id="Q_NETF_01",
        relevant_concept_ids=["net_force"],
        first_error_concept_id="net_force",
        first_error_step_order=2,
        identified_error_category="conceptual_error",
        candidate_misconception_ids=["PHY_M008"],
        posterior_hypotheses={"PHY_M008": 0.85, "unknown_or_other": 0.15},
        diagnostic_status="sufficient_evidence",
        prerequisite_concepts_to_review=["force"],
        evidence_confidence=0.90,
    )
    learner.update_from_diagnosis_export(export)

    dash = teacher_svc.get_teacher_dashboard()
    assert dash.total_students == 2
    assert dash.class_average_proficiency > 0
    assert len(dash.concept_heatmaps) == 23
    assert len(dash.frequent_misconceptions) >= 1
    assert dash.frequent_misconceptions[0]["misconception_id"] == "PHY_M008"
    assert len(dash.students_at_risk) >= 1
    assert len(dash.actionable_teaching_insights) >= 1
