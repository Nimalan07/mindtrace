import pytest

from backend.app.adaptive_learning.bkt_model import BKTModel, BKTParameters


@pytest.fixture
def bkt() -> BKTModel:
    return BKTModel(
        BKTParameters(
            p_l0=0.25,
            p_t=0.15,
            p_g=0.20,
            p_s=0.10,
        )
    )


def test_bkt_correct_observation_increases_mastery(bkt: BKTModel):
    prior = 0.25
    result = bkt.update_mastery(current_p_l=prior, is_correct=True, concept_id="net_force")
    assert result.updated_mastery > prior
    assert result.is_correct is True
    # For prior=0.25, p_s=0.1, p_g=0.2:
    # num = 0.25 * 0.9 = 0.225
    # den = 0.225 + 0.75 * 0.2 = 0.225 + 0.15 = 0.375
    # p_l_obs = 0.225 / 0.375 = 0.60
    # p_l_next = 0.60 + 0.40 * 0.15 = 0.66
    assert abs(result.updated_mastery - 0.66) < 0.02


def test_bkt_incorrect_observation_decreases_mastery(bkt: BKTModel):
    prior = 0.60
    result = bkt.update_mastery(current_p_l=prior, is_correct=False, concept_id="net_force")
    assert result.posterior_given_obs < prior


def test_bkt_repeated_practice_approaches_ceiling(bkt: BKTModel):
    mastery = 0.25
    for i in range(5):
        res = bkt.update_mastery(current_p_l=mastery, is_correct=True, concept_id="net_force")
        mastery = res.updated_mastery
    assert mastery > 0.90


def test_calibrate_from_diagnosis_direction_sign_error(bkt: BKTModel):
    calib = bkt.calibrate_from_diagnosis(
        error_category="direction_or_sign_error",
        evidence_confidence=0.85,
        has_dominant_misconception=False,
    )
    # Direction/sign slip should calibrate high slip probability
    assert calib["p_s"] > bkt.default_params.p_s
    assert calib["confidence_weight"] == 0.85


def test_calibrate_from_diagnosis_conceptual_misconception(bkt: BKTModel):
    calib = bkt.calibrate_from_diagnosis(
        error_category="conceptual_error",
        evidence_confidence=0.90,
        has_dominant_misconception=True,
    )
    # Deep conceptual error should have low slip probability
    assert calib["p_s"] < bkt.default_params.p_s
