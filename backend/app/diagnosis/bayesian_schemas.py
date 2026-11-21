import math
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

ResponseCategory = Literal[
    "supports_hypothesis",
    "weakens_hypothesis",
    "neutral_or_inconclusive",
]

CalibrationStatus = Literal[
    "illustrative",
    "expert_estimated",
    "empirically_calibrated",
]

SessionStatus = Literal[
    "collecting_evidence",
    "sufficient_evidence",
    "inconclusive",
    "no_available_questions",
]


class HypothesisBelief(BaseModel):
    """Belief state for a candidate misconception hypothesis."""

    model_config = ConfigDict(extra="forbid")

    misconception_id: str = Field(min_length=1)
    prior_probability: float = Field(ge=0.0, le=1.0)
    posterior_probability: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)


class ResponseLikelihood(BaseModel):
    """Single response category likelihood entry."""

    model_config = ConfigDict(extra="forbid")

    response_category: ResponseCategory
    likelihood: float = Field(ge=0.0, le=1.0)
    calibration_status: CalibrationStatus = "illustrative"
    evidence_source: str = Field(min_length=1)


class DiagnosticQuestionModel(BaseModel):
    """Diagnostic follow-up question with associated response likelihood models."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    target_hypotheses: List[str] = Field(min_length=1)
    response_likelihoods: Dict[str, Dict[ResponseCategory, float]] = Field(
        description="Maps hypothesis_id -> {response_category: likelihood}. Must sum to ~1.0 per hypothesis."
    )
    asked_before: bool = False
    calibration_status: CalibrationStatus = "illustrative"

    @model_validator(mode="after")
    def validate_likelihood_distributions(self):
        for hyp_id, dist in self.response_likelihoods.items():
            for cat, val in dist.items():
                if not math.isfinite(val) or val < 0.0 or val > 1.0:
                    raise ValueError(
                        f"Likelihood for {hyp_id} - {cat} must be a finite float in [0.0, 1.0]."
                    )
            total = sum(dist.values())
            if not math.isclose(total, 1.0, abs_tol=1e-3):
                raise ValueError(
                    f"Likelihood distribution for hypothesis '{hyp_id}' across response categories "
                    f"must sum to 1.0 (got {total:.4f})."
                )
        return self


class EvidenceObservation(BaseModel):
    """Recorded observation of student response to a diagnostic question."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    original_student_response: str = Field(description="Verbatim student answer string.")
    response_category: ResponseCategory
    evidence_text: str = Field(min_length=1, description="Verbatim text fragment supporting this classification.")
    interpretation_confidence: float = Field(ge=0.0, le=1.0)
    sequence_number: int = Field(ge=1)
    timestamp: Optional[str] = None


class BayesianUpdateResult(BaseModel):
    """Result of updating candidate hypothesis beliefs with new evidence."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_beliefs: List[HypothesisBelief]
    evidence_observation: EvidenceObservation
    entropy_before: float
    entropy_after: float
    posterior_distribution: Dict[str, float]
    update_status: str
    uncertainty_notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_distribution_validity(self):
        for p in self.posterior_distribution.values():
            if not math.isfinite(p) or p < 0.0 or p > 1.0:
                raise ValueError("Posterior probabilities must be finite floats in [0.0, 1.0].")
        total = sum(self.posterior_distribution.values())
        if not math.isclose(total, 1.0, abs_tol=1e-3):
            raise ValueError(f"Posterior distribution must sum to 1.0 (got {total:.4f}).")
        return self


class DiagnosticSession(BaseModel):
    """Auditable state of an active diagnostic session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    candidate_hypotheses: List[str] = Field(min_length=1)
    hypothesis_beliefs: Dict[str, HypothesisBelief]
    evidence_history: List[EvidenceObservation] = Field(default_factory=list)
    asked_question_ids: List[str] = Field(default_factory=list)
    session_status: SessionStatus = "collecting_evidence"

    @model_validator(mode="after")
    def validate_session_integrity(self):
        if set(self.candidate_hypotheses) != set(self.hypothesis_beliefs.keys()):
            raise ValueError("Candidate hypotheses list must match hypothesis beliefs keys.")
        priors_total = sum(b.posterior_probability for b in self.hypothesis_beliefs.values())
        if not math.isclose(priors_total, 1.0, abs_tol=1e-3):
            raise ValueError(f"Current hypothesis beliefs must sum to 1.0 (got {priors_total:.4f}).")
        return self
