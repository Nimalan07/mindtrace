import math
import pytest
from pydantic import ValidationError

from backend.app.diagnosis.bayesian_engine import BayesianEngine
from backend.app.diagnosis.bayesian_schemas import (
    DiagnosticQuestionModel,
    DiagnosticSession,
    EvidenceObservation,
    HypothesisBelief,
)


@pytest.fixture
def bayesian_engine():
    return BayesianEngine(posterior_threshold=0.80, min_evidence_count=2)


# 1. Uniform prior initialization
def test_uniform_prior_initialization(bayesian_engine):
    candidates = ["PHY_M009", "PHY_M002"]
    session = bayesian_engine.initialize_session(
        session_id="S001",
        candidate_hypotheses=candidates,
        include_unknown=True,
    )
    # 2 candidates + 1 unknown_or_other = 3 hypotheses
    assert len(session.hypothesis_beliefs) == 3
    assert math.isclose(session.hypothesis_beliefs["PHY_M009"].prior_probability, 1 / 3, abs_tol=1e-4)
    assert math.isclose(session.hypothesis_beliefs["PHY_M002"].prior_probability, 1 / 3, abs_tol=1e-4)
    assert math.isclose(session.hypothesis_beliefs["unknown_or_other"].prior_probability, 1 / 3, abs_tol=1e-4)


# 2. Custom prior initialization
def test_custom_prior_initialization(bayesian_engine):
    candidates = ["PHY_M009", "PHY_M002"]
    custom_priors = {
        "PHY_M009": 0.6,
        "PHY_M002": 0.4,
    }
    session = bayesian_engine.initialize_session(
        session_id="S002",
        candidate_hypotheses=candidates,
        custom_priors=custom_priors,
        include_unknown=False,
    )
    assert math.isclose(session.hypothesis_beliefs["PHY_M009"].prior_probability, 0.6)
    assert math.isclose(session.hypothesis_beliefs["PHY_M002"].prior_probability, 0.4)


# 3. Prior normalization
def test_prior_normalization(bayesian_engine):
    candidates = ["H1", "H2"]
    # Unnormalized inputs: sum is 10.0
    custom_priors = {"H1": 3.0, "H2": 7.0}
    session = bayesian_engine.initialize_session(
        session_id="S003",
        candidate_hypotheses=candidates,
        custom_priors=custom_priors,
        include_unknown=False,
    )
    assert math.isclose(session.hypothesis_beliefs["H1"].prior_probability, 0.3)
    assert math.isclose(session.hypothesis_beliefs["H2"].prior_probability, 0.7)


# 4. Posterior update using Bayes' theorem (Required Demonstration)
def test_bayes_update_demonstration(bayesian_engine):
    """
    Demonstration from Requirement 11:
    H1: Student believes interaction force depends on mass.
    H2: Student confuses force magnitude with acceleration.
    Priors: P(H1) = 0.5, P(H2) = 0.5
    Illustrative likelihoods: P(E|H1) = 0.20, P(E|H2) = 0.90
    Expected posterior:
    P(H1|E) approx 0.182
    P(H2|E) approx 0.818
    """
    candidates = ["H1_mass_force", "H2_force_accel"]
    session = bayesian_engine.initialize_session(
        session_id="S_DEMO",
        candidate_hypotheses=candidates,
        custom_priors={"H1_mass_force": 0.5, "H2_force_accel": 0.5},
        include_unknown=False,
    )

    observation = EvidenceObservation(
        question_id="DQ_DEMO",
        original_student_response="The car accelerates more because it has less mass under equal force.",
        response_category="supports_hypothesis",
        evidence_text="accelerates more",
        interpretation_confidence=0.95,
        sequence_number=1,
    )

    # Illustrative likelihoods: P(E|H1) = 0.20, P(E|H2) = 0.90
    question_likelihoods = {
        "H1_mass_force": {
            "supports_hypothesis": 0.20,
            "weakens_hypothesis": 0.80,
            "neutral_or_inconclusive": 0.0,
        },
        "H2_force_accel": {
            "supports_hypothesis": 0.90,
            "weakens_hypothesis": 0.10,
            "neutral_or_inconclusive": 0.0,
        },
    }

    result = bayesian_engine.update(session, observation, question_likelihoods)

    p_h1 = result.posterior_distribution["H1_mass_force"]
    p_h2 = result.posterior_distribution["H2_force_accel"]

    # Verify expected values (0.10 / 0.55 = 0.1818, 0.45 / 0.55 = 0.8181)
    assert round(p_h1, 3) == 0.182
    assert round(p_h2, 3) == 0.818
    assert math.isclose(p_h1 + p_h2, 1.0)


# 5. Competing hypotheses updating over multiple steps
def test_competing_hypotheses_sequential_update(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_SEQ",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )

    obs1 = EvidenceObservation(
        question_id="Q1",
        original_student_response="Evidence 1",
        response_category="supports_hypothesis",
        evidence_text="Evidence 1",
        interpretation_confidence=0.9,
        sequence_number=1,
    )
    q1_likelihoods = {
        "H1": {"supports_hypothesis": 0.8, "weakens_hypothesis": 0.2, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.2, "weakens_hypothesis": 0.8, "neutral_or_inconclusive": 0.0},
    }
    res1 = bayesian_engine.update(session, obs1, q1_likelihoods)
    assert res1.posterior_distribution["H1"] == 0.8

    obs2 = EvidenceObservation(
        question_id="Q2",
        original_student_response="Evidence 2",
        response_category="supports_hypothesis",
        evidence_text="Evidence 2",
        interpretation_confidence=0.9,
        sequence_number=2,
    )
    q2_likelihoods = {
        "H1": {"supports_hypothesis": 0.9, "weakens_hypothesis": 0.1, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.1, "weakens_hypothesis": 0.9, "neutral_or_inconclusive": 0.0},
    }
    res2 = bayesian_engine.update(session, obs2, q2_likelihoods)
    # H1 prior was 0.8, likelihood 0.9 -> 0.72. H2 prior was 0.2, likelihood 0.1 -> 0.02.
    # Total = 0.74. P(H1) = 0.72 / 0.74 = 0.973
    assert res2.posterior_distribution["H1"] > 0.95


# 6. Neutral evidence observation
def test_neutral_evidence_observation(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_NEUTRAL",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )
    obs = EvidenceObservation(
        question_id="Q_NEUTRAL",
        original_student_response="I have no idea.",
        response_category="neutral_or_inconclusive",
        evidence_text="no idea",
        interpretation_confidence=0.5,
        sequence_number=1,
    )
    # Likelihood is equal for both under neutral
    q_likelihoods = {
        "H1": {"supports_hypothesis": 0.45, "weakens_hypothesis": 0.45, "neutral_or_inconclusive": 0.1},
        "H2": {"supports_hypothesis": 0.45, "weakens_hypothesis": 0.45, "neutral_or_inconclusive": 0.1},
    }
    res = bayesian_engine.update(session, obs, q_likelihoods)
    assert math.isclose(res.posterior_distribution["H1"], 0.5)
    assert math.isclose(res.posterior_distribution["H2"], 0.5)


# 7. Zero-likelihood handling
def test_zero_likelihood_handling(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_ZERO",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )
    obs = EvidenceObservation(
        question_id="Q_ZERO",
        original_student_response="Impossible for H1",
        response_category="weakens_hypothesis",
        evidence_text="Impossible",
        interpretation_confidence=0.9,
        sequence_number=1,
    )
    q_likelihoods = {
        "H1": {"supports_hypothesis": 1.0, "weakens_hypothesis": 0.0, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.5, "weakens_hypothesis": 0.5, "neutral_or_inconclusive": 0.0},
    }
    res = bayesian_engine.update(session, obs, q_likelihoods)
    assert res.posterior_distribution["H1"] == 0.0
    assert res.posterior_distribution["H2"] == 1.0


# 8. Numerical stability with extreme values
def test_numerical_stability(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_NUM",
        candidate_hypotheses=["H1", "H2"],
        custom_priors={"H1": 1e-6, "H2": 1.0 - 1e-6},
        include_unknown=False,
    )
    obs = EvidenceObservation(
        question_id="Q_NUM",
        original_student_response="Response",
        response_category="supports_hypothesis",
        evidence_text="Response",
        interpretation_confidence=0.9,
        sequence_number=1,
    )
    q_likelihoods = {
        "H1": {"supports_hypothesis": 1e-5, "weakens_hypothesis": 0.999, "neutral_or_inconclusive": 0.001},
        "H2": {"supports_hypothesis": 1e-5, "weakens_hypothesis": 0.999, "neutral_or_inconclusive": 0.001},
    }
    res = bayesian_engine.update(session, obs, q_likelihoods)
    assert all(math.isfinite(p) for p in res.posterior_distribution.values())
    assert math.isclose(sum(res.posterior_distribution.values()), 1.0)


# 9. Probability distribution sums to one
def test_posterior_distribution_sums_to_one(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_SUM",
        candidate_hypotheses=["H1", "H2", "H3"],
        include_unknown=True,
    )
    obs = EvidenceObservation(
        question_id="Q_SUM",
        original_student_response="Resp",
        response_category="supports_hypothesis",
        evidence_text="Resp",
        interpretation_confidence=0.8,
        sequence_number=1,
    )
    q_likelihoods = {
        "H1": {"supports_hypothesis": 0.7, "weakens_hypothesis": 0.2, "neutral_or_inconclusive": 0.1},
        "H2": {"supports_hypothesis": 0.3, "weakens_hypothesis": 0.5, "neutral_or_inconclusive": 0.2},
        "H3": {"supports_hypothesis": 0.1, "weakens_hypothesis": 0.8, "neutral_or_inconclusive": 0.1},
        "unknown_or_other": {"supports_hypothesis": 0.33, "weakens_hypothesis": 0.33, "neutral_or_inconclusive": 0.34},
    }
    res = bayesian_engine.update(session, obs, q_likelihoods)
    assert math.isclose(sum(res.posterior_distribution.values()), 1.0, abs_tol=1e-4)


# 10. Repeated evidence rejection
def test_repeated_evidence_rejection(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_REP",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )
    obs = EvidenceObservation(
        question_id="Q_SAME",
        original_student_response="Resp",
        response_category="supports_hypothesis",
        evidence_text="Resp",
        interpretation_confidence=0.8,
        sequence_number=1,
    )
    q_likelihoods = {
        "H1": {"supports_hypothesis": 0.8, "weakens_hypothesis": 0.2, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.2, "weakens_hypothesis": 0.8, "neutral_or_inconclusive": 0.0},
    }
    bayesian_engine.update(session, obs, q_likelihoods)

    # Re-submitting the exact same question must be rejected
    with pytest.raises(ValueError) as exc_info:
        bayesian_engine.update(session, obs, q_likelihoods)
    assert "already been processed" in str(exc_info.value)


# 11. Evidence history preservation
def test_evidence_history_preservation(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_HIST",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )
    obs = EvidenceObservation(
        question_id="Q_HIST",
        original_student_response="Verbatim student answer here.",
        response_category="weakens_hypothesis",
        evidence_text="Verbatim student",
        interpretation_confidence=0.9,
        sequence_number=1,
    )
    q_likelihoods = {
        "H1": {"supports_hypothesis": 0.5, "weakens_hypothesis": 0.5, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.5, "weakens_hypothesis": 0.5, "neutral_or_inconclusive": 0.0},
    }
    bayesian_engine.update(session, obs, q_likelihoods)
    assert len(session.evidence_history) == 1
    assert session.evidence_history[0].original_student_response == "Verbatim student answer here."


# 12. Unknown/other hypothesis support
def test_unknown_or_other_hypothesis_support(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_UNK",
        candidate_hypotheses=["H1"],
        include_unknown=True,
    )
    assert "unknown_or_other" in session.candidate_hypotheses
    assert "unknown_or_other" in session.hypothesis_beliefs


# 13. Stopping criteria (collecting -> sufficient)
def test_stopping_criteria(bayesian_engine):
    session = bayesian_engine.initialize_session(
        session_id="S_STOP",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )
    assert session.session_status == "collecting_evidence"

    # Step 1: posterior reaches 0.8, but evidence count = 1 (min required = 2)
    obs1 = EvidenceObservation(
        question_id="Q1",
        original_student_response="Resp 1",
        response_category="supports_hypothesis",
        evidence_text="Resp 1",
        interpretation_confidence=0.9,
        sequence_number=1,
    )
    q_likes = {
        "H1": {"supports_hypothesis": 0.8, "weakens_hypothesis": 0.2, "neutral_or_inconclusive": 0.0},
        "H2": {"supports_hypothesis": 0.2, "weakens_hypothesis": 0.8, "neutral_or_inconclusive": 0.0},
    }
    bayesian_engine.update(session, obs1, q_likes)
    assert session.session_status == "collecting_evidence"

    # Step 2: second evidence confirms H1 -> evidence count reaches 2, posterior >= 0.80
    obs2 = EvidenceObservation(
        question_id="Q2",
        original_student_response="Resp 2",
        response_category="supports_hypothesis",
        evidence_text="Resp 2",
        interpretation_confidence=0.9,
        sequence_number=2,
    )
    bayesian_engine.update(session, obs2, q_likes)
    assert session.session_status == "sufficient_evidence"


# 14. Invalid probability rejection in schemas
def test_invalid_probability_rejection():
    with pytest.raises(ValidationError):
        HypothesisBelief(
            misconception_id="H1",
            prior_probability=1.5,  # > 1.0 invalid
            posterior_probability=0.5,
            evidence_count=0,
        )


# 15. Illustrative vs calibrated likelihood metadata
def test_illustrative_vs_calibrated_likelihood_metadata():
    q_model = DiagnosticQuestionModel(
        question_id="DQ_TEST",
        question_text="Diagnostic probe?",
        target_hypotheses=["H1"],
        response_likelihoods={
            "H1": {
                "supports_hypothesis": 0.7,
                "weakens_hypothesis": 0.2,
                "neutral_or_inconclusive": 0.1,
            }
        },
        calibration_status="illustrative",
    )
    assert q_model.calibration_status == "illustrative"
