from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.adaptive_learning.assessment_schemas import QuestionModel


class InterventionType(str, Enum):
    PREREQUISITE_REPAIR = "prerequisite_repair"
    MISCONCEPTION_REMEDIATION = "misconception_remediation"
    PROCEDURAL_CALIBRATION = "procedural_calibration"
    REINFORCEMENT = "reinforcement"


class InterventionStage(BaseModel):
    """Individual step within a multi-stage personalized intervention plan."""

    model_config = ConfigDict(extra="forbid")

    stage_order: int
    stage_name: str
    target_concept: str
    instructional_content: str
    suggested_action: str
    reference_question: Optional[QuestionModel] = None


class InterventionPlan(BaseModel):
    """
    Complete personalized intervention contract generated from Member 1 diagnosis export.
    Guides the student through targeted knowledge repair and practice.
    """

    model_config = ConfigDict(extra="forbid")

    student_id: str
    session_id: str
    target_concept_id: str
    intervention_type: InterventionType
    identified_misconception_id: Optional[str] = None
    identified_misconception_title: Optional[str] = None
    misconception_probability: float = 0.0
    diagnostic_confidence: float = Field(ge=0.0, le=1.0)
    prerequisite_repair_chain: List[str] = Field(default_factory=list)
    stages: List[InterventionStage] = Field(default_factory=list)
    actionable_summary: List[str] = Field(default_factory=list)
