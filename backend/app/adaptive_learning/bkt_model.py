from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class BKTParameters(BaseModel):
    """Bayesian Knowledge Tracing (BKT) configuration parameters per concept."""

    model_config = ConfigDict(extra="forbid")

    p_l0: float = Field(default=0.25, ge=0.0, le=1.0, description="Prior probability of mastery")
    p_t: float = Field(default=0.15, ge=0.0, le=1.0, description="Transition/learning probability")
    p_g: float = Field(default=0.20, ge=0.0, le=1.0, description="Guess probability")
    p_s: float = Field(default=0.10, ge=0.0, le=1.0, description="Slip probability")


class BKTUpdateResult(BaseModel):
    """Result of a Bayesian Knowledge Tracing update."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str
    prior_mastery: float
    posterior_given_obs: float
    updated_mastery: float
    is_correct: bool
    effective_p_s: float
    effective_p_g: float
    opportunity_index: int
    update_notes: str


class BKTModel:
    """
    Standard Bayesian Knowledge Tracing (Corbett & Anderson) with evidence-driven
    parameter calibration from Member 1 diagnosis exports.
    """

    def __init__(self, default_params: Optional[BKTParameters] = None) -> None:
        self.default_params = default_params or BKTParameters()

    def update_mastery(
        self,
        current_p_l: float,
        is_correct: bool,
        concept_id: str = "unknown",
        opportunity_index: int = 1,
        params: Optional[BKTParameters] = None,
        custom_slip: Optional[float] = None,
        custom_guess: Optional[float] = None,
        confidence_weight: float = 1.0,
    ) -> BKTUpdateResult:
        """
        Execute classical 2-state Hidden Markov Model BKT update.
        
        P(L | obs):
          Correct:   P(L)(1 - P_s) / [ P(L)(1 - P_s) + (1 - P(L)) P_g ]
          Incorrect: P(L) P_s / [ P(L) P_s + (1 - P(L)) (1 - P_g) ]
        
        P(L_{t+1}) = P(L | obs) + (1 - P(L | obs)) * P_t
        """
        p = params or self.default_params
        p_s = custom_slip if custom_slip is not None else p.p_s
        p_g = custom_guess if custom_guess is not None else p.p_g
        p_t = p.p_t

        # Clamp probabilities to prevent division by zero or degenerate boundaries
        p_l = max(0.001, min(0.999, current_p_l))
        p_s = max(0.01, min(0.49, p_s))
        p_g = max(0.01, min(0.49, p_g))

        if is_correct:
            numerator = p_l * (1.0 - p_s)
            denominator = numerator + (1.0 - p_l) * p_g
            p_l_obs = numerator / max(1e-9, denominator)
            notes = "Correct answer observed; mastery increased."
        else:
            numerator = p_l * p_s
            denominator = numerator + (1.0 - p_l) * (1.0 - p_g)
            p_l_obs = numerator / max(1e-9, denominator)
            notes = "Incorrect answer observed; mastery decreased based on slip/guess calibration."

        # If confidence weighting is less than 1.0, temper the update toward prior
        if confidence_weight < 1.0:
            p_l_obs = (confidence_weight * p_l_obs) + ((1.0 - confidence_weight) * p_l)
            notes += f" Tempered with evidence confidence {confidence_weight:.2f}."

        # Transition step: learning occurs from the practice opportunity
        p_l_next = p_l_obs + (1.0 - p_l_obs) * p_t
        p_l_next = max(0.01, min(0.99, p_l_next))

        return BKTUpdateResult(
            concept_id=concept_id,
            prior_mastery=round(current_p_l, 4),
            posterior_given_obs=round(p_l_obs, 4),
            updated_mastery=round(p_l_next, 4),
            is_correct=is_correct,
            effective_p_s=round(p_s, 4),
            effective_p_g=round(p_g, 4),
            opportunity_index=opportunity_index,
            update_notes=notes,
        )

    def calibrate_from_diagnosis(
        self,
        error_category: Optional[str],
        evidence_confidence: float,
        has_dominant_misconception: bool,
    ) -> Dict[str, float]:
        """
        Derive calibrated slip and guess parameters from Member 1 diagnosis metadata.
        
        Prevents arbitrary deductions by reflecting the nature of the error:
        - Minor calculation/sign slips preserve a higher slip probability P(S), so high
          priors don't erroneously crash.
        - Deep conceptual errors and verified misconceptions assign low P(S),
          accurately reflecting the lack of true mastery.
        """
        base_s = self.default_params.p_s
        base_g = self.default_params.p_g

        if error_category in ("direction_or_sign_error", "calculation_error", "mathematical_error"):
            # High slip probability (the student likely knew the core concept but made a procedural slip)
            calibrated_s = min(0.40, base_s + 0.25)
            calibrated_g = base_g
        elif error_category in ("conceptual_error", "misconception_application") or has_dominant_misconception:
            # Low slip probability (the error is rooted in genuine conceptual deficit)
            calibrated_s = max(0.04, base_s * 0.5)
            calibrated_g = min(0.30, base_g * 1.2)
        else:
            calibrated_s = base_s
            calibrated_g = base_g

        return {
            "p_s": calibrated_s,
            "p_g": calibrated_g,
            "confidence_weight": max(0.2, min(1.0, evidence_confidence)),
        }
