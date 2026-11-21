from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# ---------------------------------------------------------------------------
# Benchmark Diagnostic Tasks Catalog
# ---------------------------------------------------------------------------

_DIAGNOSTIC_TASKS_CACHE = None


def _get_diagnostic_tasks() -> List[Dict[str, Any]]:
    global _DIAGNOSTIC_TASKS_CACHE
    if _DIAGNOSTIC_TASKS_CACHE is None:
        path = Path("data/questions/diagnostic_rubrics.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _DIAGNOSTIC_TASKS_CACHE = json.load(f).get("diagnostic_tasks", [])
        else:
            _DIAGNOSTIC_TASKS_CACHE = []
    return _DIAGNOSTIC_TASKS_CACHE


@app.get(
    "/api/diagnosis/questions",
    tags=["Member 1: Diagnosis"],
    status_code=status.HTTP_200_OK,
)
def get_diagnostic_questions() -> List[Dict[str, Any]]:
    """Retrieve all benchmark diagnostic assessment tasks with structured rubrics."""
    return _get_diagnostic_tasks()


@app.get(
    "/api/diagnosis/questions/{concept_id}",
    tags=["Member 1: Diagnosis"],
    status_code=status.HTTP_200_OK,
)
def get_diagnostic_question_for_concept(concept_id: str) -> Dict[str, Any]:
    """Retrieve the optimal benchmark diagnostic task and rubric for a given concept."""
    tasks = _get_diagnostic_tasks()
    for task in tasks:
        if task.get("concept_id") == concept_id:
            return task
    for task in tasks:
        if concept_id in task.get("relevant_concept_ids", []):
            return task
    if tasks:
        return tasks[0]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No diagnostic questions available.")


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


# ===========================================================================
# Phase 5 Client Compatibility Route Aliases & Direct Endpoints
# ===========================================================================

@app.post(
    "/api/adaptive/next-question",
    response_model=AdaptiveNextQuestionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Adaptive Assessment"],
)
def next_question_alias(request: AdaptiveNextQuestionRequest) -> AdaptiveNextQuestionResponse:
    return get_next_question(request)


@app.post(
    "/api/adaptive/submit-answer",
    response_model=AssessmentEvaluation,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Adaptive Assessment"],
)
def submit_answer_alias(request: AssessmentAnswerRequest) -> AssessmentEvaluation:
    return submit_assessment(request)


@app.get(
    "/api/adaptive/learner/{student_id}",
    response_model=StudentAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analytics Dashboards"],
)
def get_learner_alias(student_id: str) -> StudentAnalyticsResponse:
    return get_student_analytics(student_id)


@app.get(
    "/api/adaptive/due-reviews/{student_id}",
    response_model=List[SpacedRepetitionCard],
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Spaced Repetition"],
)
def due_reviews_alias(student_id: str) -> List[SpacedRepetitionCard]:
    return get_due_spaced_cards(student_id)


@app.post(
    "/api/adaptive/spaced-review",
    response_model=SpacedRepetitionCard,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Spaced Repetition"],
)
def spaced_review_alias(request: SpacedReviewRequest) -> SpacedRepetitionCard:
    return record_spaced_review(request)


@app.get(
    "/api/dashboard/teacher/cohort",
    response_model=TeacherAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analytics Dashboards"],
)
def teacher_cohort_alias() -> TeacherAnalyticsResponse:
    return get_teacher_analytics()


@app.get(
    "/api/adaptive/intervention/{student_id}/{concept_id}",
    response_model=InterventionPlan,
    status_code=status.HTTP_200_OK,
    tags=["Member 2: Personalized Intervention"],
)
def get_intervention_for_concept(student_id: str, concept_id: str) -> InterventionPlan:
    """Generate or retrieve a targeted intervention plan for a student concept deficit."""
    adapt_service = get_adaptive_service()
    export = Member2DiagnosisExport(
        student_id=student_id,
        session_id=f"auto_{student_id}_{concept_id}",
        question_id=f"DEFICIT_{concept_id.upper()}",
        relevant_concept_ids=[concept_id],
        first_error_concept_id=concept_id,
        first_error_step_order=1,
        identified_error_category="conceptual_error",
        candidate_misconception_ids=[],
        posterior_hypotheses={"unknown_or_other": 1.0},
        diagnostic_status="collecting_evidence",
        prerequisite_concepts_to_review=adapt_service.concept_graph.get_direct_prerequisites(concept_id),
        evidence_confidence=0.75,
    )
    return adapt_service.generate_intervention(export)
