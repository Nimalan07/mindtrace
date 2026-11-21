from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiagnosticQuestion(BaseModel):
    """Discriminative question designed to test for a specific misconception."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    supporting_evidence: str = Field(
        min_length=1,
        description="Response pattern that increases belief in this candidate hypothesis.",
    )
    weakening_evidence: str = Field(
        min_length=1,
        description="Response pattern that decreases belief in this candidate hypothesis.",
    )


class MisconceptionRecord(BaseModel):
    """
    Expert-authored candidate misconception definition.
    
    NOTE: These entries represent expert-authored diagnostic hypotheses,
    not empirically validated student behavior. They must not be treated
    as confirmed diagnoses without multi-step evidence verification.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    associated_concepts: list[str] = Field(min_length=1)
    incorrect_belief: str = Field(min_length=1)
    correct_understanding: str = Field(min_length=1)
    typical_reasoning: list[str] = Field(min_length=1)
    common_symptoms: list[str] = Field(min_length=1)
    possible_causes: list[str] = Field(min_length=1)
    diagnostic_questions: list[DiagnosticQuestion] = Field(min_length=1)
    severity: Literal["high", "medium", "low"]

    @model_validator(mode="after")
    def validate_record_integrity(self):
        # Reject duplicate associated concepts within a single record
        if len(self.associated_concepts) != len(set(self.associated_concepts)):
            raise ValueError(
                f"Duplicate concept references found in misconception '{self.id}'."
            )

        # Check for duplicate diagnostic question IDs within this record
        q_ids = [q.question_id for q in self.diagnostic_questions]
        if len(q_ids) != len(set(q_ids)):
            raise ValueError(
                f"Duplicate diagnostic question IDs found in misconception '{self.id}'."
            )
        return self


class MisconceptionCatalogData(BaseModel):
    """Complete subject-specific misconception catalog configuration."""

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    misconceptions: list[MisconceptionRecord]

    @model_validator(mode="after")
    def validate_catalog_integrity(self):
        # Check for duplicate misconception IDs across catalog
        misconception_ids = [m.id for m in self.misconceptions]
        if len(misconception_ids) != len(set(misconception_ids)):
            raise ValueError("Duplicate misconception IDs found in catalog.")

        # Check for duplicate question IDs across the entire catalog
        all_question_ids: list[str] = []
        for m in self.misconceptions:
            for q in m.diagnostic_questions:
                if q.question_id in all_question_ids:
                    raise ValueError(
                        f"Duplicate diagnostic question ID '{q.question_id}' "
                        f"detected in misconception '{m.id}'."
                    )
                all_question_ids.append(q.question_id)
        return self
