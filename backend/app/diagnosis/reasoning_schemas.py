from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

ReasoningType = Literal[
    "factual_claim",
    "conceptual_assumption",
    "formula_selection",
    "mathematical_operation",
    "inference",
    "conclusion",
    "unknown",
]

ExtractionStatus = Literal[
    "complete",
    "partial",
    "insufficient_information",
]


class ReasoningStep(BaseModel):
    """
    Structured representation of a single extracted reasoning step.
    
    Preserves what the student explicitly asserted without fabricating
    intermediate assumptions or conclusions.
    """

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, description="Unique identifier for this step within an extraction.")
    order: int = Field(ge=1, description="1-indexed sequence order of the reasoning step.")
    original_text: str = Field(min_length=1, description="Original text fragment from which this step was extracted.")
    claim: str = Field(min_length=1, description="Normalized claim or assertion made in this step.")
    reasoning_type: ReasoningType = Field(description="Classification of the reasoning step.")
    concept_ids: List[str] = Field(default_factory=list, description="IDs of concepts involved in this step.")
    formulas: List[str] = Field(default_factory=list, description="Formulas or equations explicitly referenced or applied.")
    inference: Optional[str] = Field(default=None, description="Logical inference connecting this step to preceding/subsequent claims.")
    evidence_text: str = Field(min_length=1, description="Exact substring from original response supporting this extraction.")
    uncertainty_flag: bool = Field(default=False, description="True if the student expresses hesitation, doubt, or ambiguous phrasing.")

    @model_validator(mode="after")
    def validate_step_integrity(self):
        # Reject duplicate concept IDs within a single step
        if len(self.concept_ids) != len(set(self.concept_ids)):
            raise ValueError(
                f"Duplicate concept IDs found in step '{self.step_id}'."
            )
        return self


class ExtractedReasoning(BaseModel):
    """
    Structured reasoning evidence extracted from a student's natural-language response.
    
    Audit-trailed to the original response; does not confirm or update misconception
    probabilities.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    original_student_response: str = Field(description="Unmodified student response string.")
    reasoning_steps: List[ReasoningStep] = Field(description="Chronological reasoning steps extracted from student explanation.")
    identified_concepts: List[str] = Field(default_factory=list)
    extraction_status: ExtractionStatus = Field(description="Completeness status of the reasoning extraction.")
    ambiguity_notes: List[str] = Field(default_factory=list, description="Diagnostic notes detailing ambiguities, omissions, or provider flags.")

    @model_validator(mode="after")
    def validate_extraction_integrity(self):
        # 1. Reject duplicate step IDs
        step_ids = [step.step_id for step in self.reasoning_steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step IDs found in reasoning extraction.")

        # 2. Reject duplicate concept IDs in identified_concepts
        if len(self.identified_concepts) != len(set(self.identified_concepts)):
            raise ValueError("Duplicate concept IDs found in identified_concepts.")

        # 3. Validate step order sequence (1, 2, 3...)
        orders = [step.order for step in self.reasoning_steps]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate step order indices found in reasoning steps.")
        if orders != sorted(orders):
            raise ValueError("Reasoning steps must be in ascending sequential order.")
        for expected_idx, order in enumerate(orders, start=1):
            if order != expected_idx:
                raise ValueError(
                    f"Reasoning steps order must be sequential starting at 1 (expected {expected_idx}, got {order})."
                )

        # 4. Validate evidence text traceability to original student response
        normalized_resp = " ".join(self.original_student_response.lower().split())
        for step in self.reasoning_steps:
            normalized_evidence = " ".join(step.evidence_text.lower().split())
            if normalized_evidence and normalized_evidence not in normalized_resp:
                raise ValueError(
                    f"Evidence text '{step.evidence_text}' in step '{step.step_id}' "
                    f"cannot be traced to the original student response."
                )

        # 5. Prevent fabricated reasoning steps for empty responses
        if not self.original_student_response.strip() and self.reasoning_steps:
            raise ValueError("Cannot have reasoning steps for an empty student response.")

        # 6. Cannot claim complete extraction with zero reasoning steps
        if self.extraction_status == "complete" and not self.reasoning_steps:
            raise ValueError("Extraction status cannot be 'complete' with zero reasoning steps.")

        return self
