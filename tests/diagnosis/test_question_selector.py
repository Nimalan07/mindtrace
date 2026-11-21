import math
from pathlib import Path
import pytest

from backend.app.diagnosis.bayesian_engine import BayesianEngine
from backend.app.diagnosis.bayesian_schemas import (
    DiagnosticQuestionModel,
    DiagnosticSession,
)
from backend.app.diagnosis.question_selector import ActiveQuestionSelector
from backend.app.diagnosis.response_interpreter import MockResponseInterpreter

LIKELIHOODS_PATH = Path("data/misconceptions/likelihoods.json")


@pytest.fixture
def bayesian_engine():
    return BayesianEngine()


@pytest.fixture
def question_selector():
    return ActiveQuestionSelector.load_from_json(LIKELIHOODS_PATH)


# 16. Entropy calculation
def test_entropy_calculation(bayesian_engine):
    # Two equiprobable outcomes: H = - (0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0 bit
    dist_equal = {"H1": 0.5, "H2": 0.5}
    h_equal = bayesian_engine.calculate_entropy(dist_equal)
    assert math.isclose(h_equal, 1.0, abs_tol=1e-4)

    # Deterministic outcome: H = 0.0 bits
    dist_certain = {"H1": 1.0, "H2": 0.0}
    h_certain = bayesian_engine.calculate_entropy(dist_certain)
    assert math.isclose(h_certain, 0.0, abs_tol=1e-4)


# 17. Information gain calculation
def test_information_gain_calculation(question_selector):
    current_dist = {"PHY_M009": 0.5, "PHY_M002": 0.5}
    q = question_selector.question_catalog[0]  # DQ_PHY_M009_1
    ig = question_selector.calculate_information_gain(current_dist, q)
    # The question strongly distinguishes M009 from M002, so IG must be positive and > 0.1 bits
    assert ig > 0.1
    assert ig <= 1.0


# 18. Best question selection
def test_best_question_selection(bayesian_engine, question_selector):
    # Competing hypotheses: PHY_M009 vs PHY_M002
    session = bayesian_engine.initialize_session(
        session_id="S_SELECT",
        candidate_hypotheses=["PHY_M009", "PHY_M002"],
        include_unknown=False,
    )

    best_q, ig, rationale = question_selector.select_best_question(session)
    assert best_q is not None
    # For Newton's Third Law (M009 vs M002), DQ_PHY_M009_1 provides the highest IG
    assert best_q.question_id == "DQ_PHY_M009_1"
    assert ig > 0.0
    assert "maximizing expected Information Gain" in rationale


# 19. Previously asked question exclusion
def test_previously_asked_question_exclusion(bayesian_engine, question_selector):
    session = bayesian_engine.initialize_session(
        session_id="S_EXCLUDE",
        candidate_hypotheses=["PHY_M009", "PHY_M002"],
        include_unknown=False,
    )
    # Mark the best question as already asked
    session.asked_question_ids.append("DQ_PHY_M009_1")

    best_q, ig, rationale = question_selector.select_best_question(session)
    assert best_q is not None
    # Must NOT select DQ_PHY_M009_1 again
    assert best_q.question_id != "DQ_PHY_M009_1"


# 20. Deterministic tie breaking
def test_deterministic_tie_breaking(bayesian_engine):
    # Create two identical questions with different IDs: "DQ_B" and "DQ_A"
    dist = {
        "H1": {"supports_hypothesis": 0.7, "weakens_hypothesis": 0.2, "neutral_or_inconclusive": 0.1},
        "H2": {"supports_hypothesis": 0.3, "weakens_hypothesis": 0.6, "neutral_or_inconclusive": 0.1},
    }
    q_b = DiagnosticQuestionModel(
        question_id="DQ_B",
        question_text="Probe B?",
        target_hypotheses=["H1", "H2"],
        response_likelihoods=dist,
    )
    q_a = DiagnosticQuestionModel(
        question_id="DQ_A",
        question_text="Probe A?",
        target_hypotheses=["H1", "H2"],
        response_likelihoods=dist,
    )

    selector = ActiveQuestionSelector(question_catalog=[q_b, q_a])
    session = bayesian_engine.initialize_session(
        session_id="S_TIE",
        candidate_hypotheses=["H1", "H2"],
        include_unknown=False,
    )

    best_q, ig, rationale = selector.select_best_question(session)
    # Even though q_b was listed first, tie-breaking selects DQ_A alphabetically
    assert best_q.question_id == "DQ_A"


# 21. Missing likelihood fallback
def test_missing_likelihood_fallback(bayesian_engine):
    q_unmodeled = DiagnosticQuestionModel(
        question_id="DQ_FALLBACK",
        question_text="Uncalibrated probe without likelihoods?",
        target_hypotheses=["H1"],
        response_likelihoods={},
    )
    selector = ActiveQuestionSelector(question_catalog=[q_unmodeled])
    session = bayesian_engine.initialize_session(
        session_id="S_FALLBACK",
        candidate_hypotheses=["H1"],
        include_unknown=False,
    )

    best_q, ig, rationale = selector.select_best_question(session)
    assert best_q.question_id == "DQ_FALLBACK"
    assert ig == 0.0
    assert "fallback" in rationale.lower()


# 22. Ambiguous response handling in response interpreter
def test_ambiguous_response_handling():
    interpreter = MockResponseInterpreter(
        canned_mappings={"truck has more force": "supports_hypothesis"},
        default_category="neutral_or_inconclusive",
    )
    q = DiagnosticQuestionModel(
        question_id="DQ_TEST",
        question_text="Question text",
        target_hypotheses=["H1"],
        response_likelihoods={},
    )

    # Explicit mapped match
    obs_clear = interpreter.interpret(q, "The truck has more force because it is heavier.", sequence_number=1)
    assert obs_clear.response_category == "supports_hypothesis"
    assert obs_clear.interpretation_confidence == 0.90

    # Ambiguous / unmapped answer -> neutral_or_inconclusive
    obs_ambig = interpreter.interpret(q, "I am really not sure what happens.", sequence_number=2)
    assert obs_ambig.response_category == "neutral_or_inconclusive"
    assert obs_ambig.interpretation_confidence == 0.50
