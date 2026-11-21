import pytest

from backend.app.adaptive_learning.intervention_engine import PersonalizedInterventionEngine
from backend.app.adaptive_learning.intervention_schemas import InterventionType
from backend.app.adaptive_learning.question_bank import QuestionBank
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


@pytest.fixture
def intervention_engine() -> PersonalizedInterventionEngine:
    cg = ConceptGraph.load_from_json("data/concepts/physics_force_motion.json")
    ml = MisconceptionLibrary.load_from_json("data/misconceptions/physics_force_motion.json", concept_graph=cg)
    qb = QuestionBank.load_from_json("data/questions/physics_questions.json", concept_graph=cg)
    return PersonalizedInterventionEngine(
        concept_graph=cg,
        misconception_library=ml,
        question_bank=qb,
    )


def test_generate_intervention_misconception(intervention_engine: PersonalizedInterventionEngine):
    export = Member2DiagnosisExport(
        student_id="student_101",
        session_id="diag_session_101",
        question_id="Q_NETF_01",
        relevant_concept_ids=["net_force", "force"],
        first_error_concept_id="net_force",
        first_error_step_order=2,
        identified_error_category="direction_or_sign_error",
        candidate_misconception_ids=["PHY_M008"],
        posterior_hypotheses={"PHY_M008": 0.8524, "unknown_or_other": 0.1476},
        diagnostic_status="sufficient_evidence",
        prerequisite_concepts_to_review=["force"],
        evidence_confidence=0.90,
    )

    plan = intervention_engine.generate_intervention(export)

    assert plan.student_id == "student_101"
    assert plan.target_concept_id == "net_force"
    assert plan.identified_misconception_id == "PHY_M008"
    assert plan.misconception_probability == 0.8524
    assert len(plan.stages) >= 3

    # Check stage names
    stage_names = [s.stage_name for s in plan.stages]
    assert any("Prerequisite" in s for s in stage_names)
    assert any("Remediation" in s for s in stage_names)
    assert any("Practice" in s for s in stage_names)

    # Check actionable summary
    assert len(plan.actionable_summary) > 0


def test_generate_intervention_prerequisite_repair(intervention_engine: PersonalizedInterventionEngine):
    export = Member2DiagnosisExport(
        student_id="student_102",
        session_id="diag_session_102",
        question_id="Q_N2L_01",
        relevant_concept_ids=["newton_second_law", "net_force"],
        first_error_concept_id="newton_second_law",
        first_error_step_order=1,
        identified_error_category="missing_prerequisite",
        candidate_misconception_ids=[],
        posterior_hypotheses={"unknown_or_other": 1.0},
        diagnostic_status="sufficient_evidence",
        prerequisite_concepts_to_review=["net_force", "force"],
        evidence_confidence=0.80,
    )

    plan = intervention_engine.generate_intervention(export)
    assert plan.intervention_type == InterventionType.PREREQUISITE_REPAIR
    assert len(plan.prerequisite_repair_chain) >= 1
