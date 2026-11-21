from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

StepStatus = Literal["correct", "incorrect", "uncertain"]

ErrorType = Literal[
    "conceptual_error",
    "formula_selection_error",
    "mathematical_error",
    "direction_or_sign_error",
    "logical_inference_error",
    "missing_prerequisite",
    "unsupported_claim",
    "unknown",
]

ConfidenceLevel = Literal["high", "medium", "low", "uncertain"]


class ExpectedStep(BaseModel):
    """An individual expected step in an expert question-solving rubric."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    expected_concept_ids: List[str] = Field(default_factory=list)
    expected_principle: str = Field(min_length=1)
    acceptable_reasoning: List[str] = Field(default_factory=list)
    acceptable_formulas: List[str] = Field(default_factory=list)
    validation_criteria: Dict[str, Any] = Field(default_factory=dict)


class QuestionRubric(BaseModel):
    """
    Expert question rubric supporting multiple valid solving paths.
    
    Decoupled from student evaluation to avoid premature or rigid single-path bias.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    expected_steps: List[ExpectedStep] = Field(min_length=1)
    accepted_alternative_methods: List[str] = Field(default_factory=list)
    expected_answer: str = Field(min_length=1)
    relevant_concept_ids: List[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rubric_integrity(self):
        step_ids = [step.step_id for step in self.expected_steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step IDs found in QuestionRubric expected steps.")
        return self


class StepEvaluation(BaseModel):
    """Evaluation result for an individual student reasoning step."""

    model_config = ConfigDict(extra="forbid")

    student_step_id: str = Field(min_length=1)
    order: int = Field(ge=1)
    status: StepStatus
    error_type: Optional[ErrorType] = None
    explanation: str = Field(min_length=1)
    evidence_text: str = Field(default="")
    affected_concepts: List[str] = Field(default_factory=list)
    is_downstream_error: bool = Field(
        default=False,
        description="True if step is incorrect purely due to propagating an earlier error.",
    )


class FirstErrorResult(BaseModel):
    """
    Diagnostic result identifying the first point of reasoning failure.
    
    Explicitly tracks downstream affected steps and candidate misconception hypotheses
    without asserting premature confirmation.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    first_error_step_id: Optional[str] = None
    first_error_order: Optional[int] = None
    error_type: Optional[ErrorType] = None
    error_explanation: Optional[str] = None
    step_evaluations: List[StepEvaluation] = Field(default_factory=list)
    downstream_affected_steps: List[str] = Field(default_factory=list)
    candidate_misconception_ids: List[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel
    uncertainty_notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_consistency(self):
        # If first_error_step_id is provided, order and error_type should be present
        if self.first_error_step_id is not None:
            if self.first_error_order is None or self.error_type is None:
                raise ValueError(
                    "first_error_order and error_type must be provided when first_error_step_id is set."
                )
        return self
