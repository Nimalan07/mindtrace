from contextlib import asynccontextmanager
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.adaptive_learning.adaptive_service import AdaptiveLearningService
from backend.app.adaptive_learning.assessment_schemas import (
    AdaptiveNextQuestionRequest,
    AdaptiveNextQuestionResponse,
    AssessmentAnswerRequest,
    AssessmentEvaluation,
)
from backend.app.adaptive_learning.intervention_schemas import InterventionPlan
from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionCard
from backend.app.dashboard.dashboard_schemas import (
    StudentAnalyticsResponse,
    TeacherAnalyticsResponse,
)
from backend.app.diagnosis.service import DiagnosisService
from backend.app.diagnosis.service_schemas import (
    ConceptListResponse,
    DiagnosisFollowupRequest,
    DiagnosisFollowupResponse,
    DiagnosisSubmitRequest,
    DiagnosisSubmitResponse,
    Member2DiagnosisExport,
)

# Global or injected service instances
_diagnosis_service: DiagnosisService | None = None
_adaptive_service: AdaptiveLearningService | None = None


def get_diagnosis_service() -> DiagnosisService:
    global _diagnosis_service
    if _diagnosis_service is None:
        _diagnosis_service = DiagnosisService.create_default()
    return _diagnosis_service


def set_diagnosis_service(service: DiagnosisService) -> None:
    global _diagnosis_service
    _diagnosis_service = service


def get_adaptive_service() -> AdaptiveLearningService:
    global _adaptive_service
    if _adaptive_service is None:
        _adaptive_service = AdaptiveLearningService.create_default()
    return _adaptive_service


def set_adaptive_service(service: AdaptiveLearningService) -> None:
    global _adaptive_service
    _adaptive_service = service


class SpacedReviewRequest(BaseModel):
    student_id: str
    concept_id: str
    quality_score: int = Field(ge=0, le=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure both Member 1 & Member 2 default services initialized
    get_diagnosis_service()
    get_adaptive_service()
    yield


app = FastAPI(
    title="MINDTRACE — Reasoning Diagnosis & Adaptive Learning Platform",
    description=(
        "Unified intelligent platform integrating Member 1 (Reasoning Diagnosis Engine) "
        "and Member 2 (Adaptive Learning, BKT Mastery, Interventions & Spaced Repetition)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Health check endpoint confirming engine readiness across all modules."""
    diag = get_diagnosis_service()
    adapt = get_adaptive_service()
    return {
        "status": "healthy",
        "service": "mindtrace-unified-platform",
        "registered_concepts": len(diag.concept_graph.get_all_concepts()),
        "registered_misconceptions": len(diag.misconception_library),
        "available_likelihood_models": len(diag.question_selector.question_catalog),
        "question_bank_size": len(adapt.question_bank.get_all_questions()),
        "tracked_students": len(adapt.learner_model._profiles),
    }


# ===========================================================================
# Member 1 — Learning Intelligence & Reasoning Diagnosis Endpoints
# ===========================================================================

@app.post(
    "/api/diagnosis/submit",
    response_model=DiagnosisSubmitResponse,
    status_code=status.HTTP_200_OK,
    tags=["Member 1: Diagnosis"],
)
def submit_diagnosis(request: DiagnosisSubmitRequest) -> DiagnosisSubmitResponse:
    """
    Submit open-ended student reasoning for initial error analysis, misconception hypothesis
    retrieval, and active follow-up probe selection.
    """
    try:
        service = get_diagnosis_service()
        return service.submit_diagnosis(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Diagnosis submission failed: {str(e)}",
        )


@app.post(
    "/api/diagnosis/followup",
    response_model=DiagnosisFollowupResponse,
    status_code=status.HTTP_200_OK,
    tags=["Member 1: Diagnosis"],
)
def process_followup(request: DiagnosisFollowupRequest) -> DiagnosisFollowupResponse:
    """
    Submit an answer to a diagnostic follow-up question to execute a sequential Bayesian update.
    """
    service = get_diagnosis_service()
    try:
        return service.process_followup(request)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get(
    "/api/diagnosis/concepts",
    response_model=ConceptListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Knowledge Graph"],
)
def get_concepts() -> ConceptListResponse:
    """Retrieve the registered Physics prerequisite concept graph topology."""
    service = get_diagnosis_service()
    return service.get_concepts()


@app.get(
    "/api/diagnosis/session/{session_id}/export",
    response_model=Member2DiagnosisExport,
    status_code=status.HTTP_200_OK,
    tags=["Member 1 -> Member 2 Integration"],
)
def export_member_2(session_id: str) -> Member2DiagnosisExport:
    """
    Retrieve clean diagnosis outputs for Member 2's adaptive learning and BKT engine.
    """
    service = get_diagnosis_service()
    try:
        return service.export_for_member_2(session_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ===========================================================================
# Member 2 — Adaptive Learning, Assessment & Intervention Endpoints
# ===========================================================================

@app.post(
    "/api/adaptive/question/next",
    response_model=AdaptiveNextQuestionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Adaptive Assessment"],
)
def get_next_question(request: AdaptiveNextQuestionRequest) -> AdaptiveNextQuestionResponse:
    """
    Retrieve the next pedagogically optimal question adapted to student mastery,
    automatically diverting to foundational prerequisites if gaps are detected.
    """
    adapt_service = get_adaptive_service()
    return adapt_service.select_next_question(request)


@app.post(
    "/api/adaptive/assessment/submit",
    response_model=AssessmentEvaluation,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Adaptive Assessment"],
)
def submit_assessment(request: AssessmentAnswerRequest) -> AssessmentEvaluation:
    """
    Submit answer to an assessment question, evaluate correctness, execute BKT
    mastery update, and update spaced repetition revision schedules.
    """
    adapt_service = get_adaptive_service()
    try:
        return adapt_service.submit_assessment_answer(request)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post(
    "/api/adaptive/intervention/generate",
    response_model=InterventionPlan,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Personalized Intervention"],
)
def generate_intervention(export: Member2DiagnosisExport) -> InterventionPlan:
    """
    Generate a personalized multi-stage intervention from a Member 1 diagnosis export.
    Calibrates BKT mastery without arbitrary penalty drops.
    """
    adapt_service = get_adaptive_service()
    return adapt_service.generate_intervention(export)


@app.post(
    "/api/adaptive/intervention/session/{session_id}",
    response_model=InterventionPlan,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Personalized Intervention"],
)
def generate_intervention_from_session(session_id: str) -> InterventionPlan:
    """
    Direct bridge endpoint: retrieves Member 1's diagnostic export for a session
    and immediately synthesizes the personalized remediation plan.
    """
    diag_service = get_diagnosis_service()
    adapt_service = get_adaptive_service()
    try:
        export = diag_service.export_for_member_2(session_id)
        return adapt_service.generate_intervention(export)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/api/adaptive/spaced-repetition/due/{student_id}",
    response_model=List[SpacedRepetitionCard],
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Spaced Repetition"],
)
def get_due_spaced_cards(student_id: str) -> List[SpacedRepetitionCard]:
    """Retrieve all spaced revision cards due for review for a student."""
    adapt_service = get_adaptive_service()
    return adapt_service.get_due_spaced_repetition(student_id)


@app.post(
    "/api/adaptive/spaced-repetition/review",
    response_model=SpacedRepetitionCard,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Spaced Repetition"],
)
def record_spaced_review(request: SpacedReviewRequest) -> SpacedRepetitionCard:
    """Record a spaced repetition review result with quality score 0..5."""
    adapt_service = get_adaptive_service()
    return adapt_service.record_spaced_repetition_review(
        student_id=request.student_id,
        concept_id=request.concept_id,
        quality_score=request.quality_score,
    )


# ===========================================================================
# Dashboard Analytics Endpoints
# ===========================================================================

@app.get(
    "/api/analytics/student/{student_id}",
    response_model=StudentAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analytics Dashboards"],
)
def get_student_analytics(student_id: str) -> StudentAnalyticsResponse:
    """Retrieve comprehensive analytics and mastery breakdown for a student."""
    adapt_service = get_adaptive_service()
    return adapt_service.get_student_analytics(student_id)


@app.get(
    "/api/analytics/teacher",
    response_model=TeacherAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analytics Dashboards"],
)
def get_teacher_analytics() -> TeacherAnalyticsResponse:
    """Retrieve classroom-level analytics, concept heatmaps, and at-risk alerts."""
    adapt_service = get_adaptive_service()
    return adapt_service.get_teacher_analytics()
