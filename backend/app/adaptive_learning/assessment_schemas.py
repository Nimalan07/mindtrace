from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERICAL = "numerical"
    CONCEPTUAL_EXPLANATION = "conceptual_explanation"


class QuestionModel(BaseModel):
    """Structured question definition in the question bank."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    prompt: str
    concept_id: str
    secondary_concept_ids: List[str] = Field(default_factory=list)
    difficulty: QuestionDifficulty
    question_type: QuestionType
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    rubric: str
    hints: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    target_misconceptions: List[str] = Field(default_factory=list)


class AssessmentAnswerRequest(BaseModel):
    """Payload submitted when a student answers an assessment question."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    question_id: str
    student_answer: str
    time_spent_seconds: Optional[float] = None
    session_id: Optional[str] = None


class AssessmentEvaluation(BaseModel):
    """Result of grading an assessment question attempt."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    student_id: str
    concept_id: str
    is_correct: bool
    score: float = Field(ge=0.0, le=1.0)
    student_answer: str
    correct_answer: str
    feedback: str
    rubric: str
    prior_mastery: float
    updated_mastery: float
    target_misconceptions: List[str] = Field(default_factory=list)
    demonstrated_misconceptions: List[str] = Field(default_factory=list)
    next_recommended_difficulty: QuestionDifficulty


class AdaptiveNextQuestionRequest(BaseModel):
    """Request for the next pedagogically optimal question."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    target_concept_id: Optional[str] = None
    exclude_question_ids: List[str] = Field(default_factory=list)
    allow_prerequisite_diversion: bool = True


class AdaptiveNextQuestionResponse(BaseModel):
    """Adaptive question recommendation returned by the difficulty engine."""

    model_config = ConfigDict(extra="forbid")

    question: Optional[QuestionModel] = None
    target_concept_id: str
    actual_question_concept_id: str
    recommended_difficulty: QuestionDifficulty
    selection_reason: str
    prerequisite_blocked: bool = False
    prerequisite_concept_id: Optional[str] = None
    current_concept_mastery: float
    overall_proficiency: float
