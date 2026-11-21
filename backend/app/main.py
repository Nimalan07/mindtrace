from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from backend.app.diagnosis.service import DiagnosisService
from backend.app.diagnosis.service_schemas import (
    ConceptListResponse,
    DiagnosisFollowupRequest,
    DiagnosisFollowupResponse,
    DiagnosisSubmitRequest,
    DiagnosisSubmitResponse,
    Member2DiagnosisExport,
)

# Global or injected service instance
_service: DiagnosisService | None = None


def get_diagnosis_service() -> DiagnosisService:
    global _service
    if _service is None:
        _service = DiagnosisService.create_default()
    return _service


def set_diagnosis_service(service: DiagnosisService) -> None:
    global _service
    _service = service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure default service initialized
    get_diagnosis_service()
    yield


app = FastAPI(
    title="MINDTRACE — Learning Intelligence & Reasoning Diagnosis Engine",
    description="Adaptive learning diagnosis API providing evidence-driven misconception verification and knowledge repair.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Health check endpoint confirming engine readiness."""
    service = get_diagnosis_service()
    return {
        "status": "healthy",
        "service": "mindtrace-diagnosis-engine",
        "registered_concepts": len(service.concept_graph.get_all_concepts()),
        "registered_misconceptions": len(service.misconception_library),
        "available_likelihood_models": len(service.question_selector.question_catalog),
    }


@app.post(
    "/api/diagnosis/submit",
    response_model=DiagnosisSubmitResponse,
    status_code=status.HTTP_200_OK,
    tags=["Diagnosis"],
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
    tags=["Diagnosis"],
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
    """
    Retrieve the registered Physics prerequisite concept graph topology.
    """
    service = get_diagnosis_service()
    return service.get_concepts()


@app.get(
    "/api/diagnosis/session/{session_id}/export",
    response_model=Member2DiagnosisExport,
    status_code=status.HTTP_200_OK,
    tags=["Member 2 Integration"],
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
