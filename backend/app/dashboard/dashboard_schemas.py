from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MasteryStatus(str, Enum):
    MASTERED = "mastered"
    PRACTICING = "practicing"
    NEEDS_SUPPORT = "needs_support"


class ConceptMasteryView(BaseModel):
    """Detailed view of a student's performance on a single concept."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str
    concept_name: str
    topic: str
    mastery_probability: float
    status: MasteryStatus
    opportunities: int
    correct_count: int


class StudentAnalyticsResponse(BaseModel):
    """Personalized learning analytics payload for student dashboard."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    overall_proficiency: float
    total_assessments: int
    total_correct: int
    accuracy_rate: float
    mastery_counts: Dict[str, int]
    concept_mastery_breakdown: List[ConceptMasteryView]
    strengths: List[str]
    critical_weaknesses: List[str]
    recommended_next_topics: List[str]
    due_revisions_count: int
    due_revisions: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class ConceptHeatmapView(BaseModel):
    """Class-level concept performance distribution."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str
    concept_name: str
    topic: str
    average_mastery: float
    struggling_students_count: int
    mastered_students_count: int


class StudentAtRiskView(BaseModel):
    """Alert record for a student requiring instructional teacher intervention."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    overall_proficiency: float
    primary_deficit_concept: str
    active_misconceptions: List[str]
    recommended_intervention: str


class TeacherAnalyticsResponse(BaseModel):
    """Class-wide diagnostic and mastery insights for the educator dashboard."""

    model_config = ConfigDict(extra="forbid")

    total_students: int
    class_average_proficiency: float
    concept_heatmaps: List[ConceptHeatmapView]
    frequent_misconceptions: List[Dict[str, Any]]
    students_at_risk: List[StudentAtRiskView]
    topic_readiness: Dict[str, float]
    actionable_teaching_insights: List[str]
