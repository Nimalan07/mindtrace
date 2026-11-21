from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.diagnosis.bayesian_schemas import (
    CalibrationStatus,
    DiagnosticQuestionModel,
    EvidenceObservation,
    ResponseCategory,
    SessionStatus,
)
from backend.app.diagnosis.error_schemas import FirstErrorResult, QuestionRubric
from backend.app.diagnosis.reasoning_schemas import ExtractedReasoning


# ---------------------------------------------------------------------------
# API Request Models
# ---------------------------------------------------------------------------

class DiagnosisSubmitRequest(BaseModel):
    """Payload for submitting an initial student response for diagnosis."""

    model_config = ConfigDict(extra="forbid")

    student_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    student_response: str = Field(description="Student's natural-language answer and reasoning.")
    rubric: QuestionRubric
    relevant_concept_ids: List[str] = Field(min_length=1)


class DiagnosisFollowupRequest(BaseModel):
    """Payload for submitting a response to a follow-up diagnostic question."""

    model_config = ConfigDict(extra="forbid")

    diagnosis_session_id: str = Field(min_length=1)
    followup_question_id: str = Field(min_length=1)
    student_response: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# API Response Models
# ---------------------------------------------------------------------------

class FollowupQuestionView(BaseModel):
    """Sanitized view of a diagnostic question presented to the student."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    question_text: str
    expected_information_gain: float
    selection_rationale: str
    calibration_status: CalibrationStatus


class DiagnosisSubmitResponse(BaseModel):
    """Response returned upon initial reasoning diagnosis."""

    model_config = ConfigDict(extra="forbid")

    diagnosis_session_id: str
    student_id: str
    question_id: str
    extracted_reasoning: ExtractedReasoning
    first_error_result: FirstErrorResult
    candidate_misconception_ids: List[str]
    posterior_hypothesis_distribution: Dict[str, float]
    selected_followup_question: Optional[FollowupQuestionView] = None
    diagnostic_status: SessionStatus
    prerequisite_concepts_to_review: List[str] = Field(default_factory=list)
    uncertainty_notes: List[str] = Field(default_factory=list)
    calibration_status: CalibrationStatus = "illustrative"


class DiagnosisFollowupResponse(BaseModel):
    """Response returned after processing a follow-up answer."""

    model_config = ConfigDict(extra="forbid")

    diagnosis_session_id: str
    interpreted_evidence: EvidenceObservation
    updated_hypothesis_distribution: Dict[str, float]
    evidence_history_count: int
    diagnostic_status: SessionStatus
    next_followup_question: Optional[FollowupQuestionView] = None
    uncertainty_notes: List[str] = Field(default_factory=list)
    calibration_status: CalibrationStatus = "illustrative"


class ConceptDetailView(BaseModel):
    """Public detail of a concept in the prerequisite graph."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    topic: str
    description: str
    prerequisites: List[str]
    related_concepts: List[str]


class ConceptListResponse(BaseModel):
    """Response returning all registered concepts and graph topology."""

    model_config = ConfigDict(extra="forbid")

    subject: str
    domain: str
    version: str
    total_concepts: int
    total_prerequisite_edges: int
    concepts: List[ConceptDetailView]


# ---------------------------------------------------------------------------
# Member 2 Integration Export Contract
# ---------------------------------------------------------------------------

class Member2DiagnosisExport(BaseModel):
    """
    Clean diagnosis output contract for Member 2's adaptive learning and BKT engine.
    
    Provides concept-level and misconception-level diagnosis without encroaching on
    mastery calculations.
    """

    model_config = ConfigDict(extra="forbid")

    student_id: str
    session_id: str
    question_id: str
    relevant_concept_ids: List[str]
    first_error_concept_id: Optional[str] = None
    first_error_step_order: Optional[int] = None
    identified_error_category: Optional[str] = None
    candidate_misconception_ids: List[str]
    posterior_hypotheses: Dict[str, float]
    diagnostic_status: SessionStatus
    prerequisite_concepts_to_review: List[str]
    evidence_confidence: float
