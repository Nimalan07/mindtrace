from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from backend.app.diagnosis.bayesian_engine import BayesianEngine
from backend.app.diagnosis.bayesian_schemas import (
    DiagnosticQuestionModel,
    DiagnosticSession,
    EvidenceObservation,
)
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.error_detector import FirstErrorDetector
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.question_selector import ActiveQuestionSelector
from backend.app.diagnosis.reasoning_extractor import (
    LLMProvider,
    MockLLMProvider,
    ReasoningExtractor,
    SmartOfflineLLMProvider,
)
from backend.app.diagnosis.response_interpreter import (
    MockResponseInterpreter,
    ResponseInterpreter,
)
from backend.app.diagnosis.service_schemas import (
    ConceptDetailView,
    ConceptListResponse,
    DiagnosisFollowupRequest,
    DiagnosisFollowupResponse,
    DiagnosisSubmitRequest,
    DiagnosisSubmitResponse,
    FollowupQuestionView,
    Member2DiagnosisExport,
)
from backend.app.diagnosis.session_repository import (
    SessionRepository,
    SQLiteSessionRepository,
)


class DiagnosisService:
    """
    Orchestration service coordinating reasoning extraction, first-error detection,
    misconception hypothesis retrieval, and Bayesian verification.
    """

    def __init__(
        self,
        concept_graph: ConceptGraph,
        misconception_library: MisconceptionLibrary,
        question_selector: ActiveQuestionSelector,
        bayesian_engine: Optional[BayesianEngine] = None,
        reasoning_extractor: Optional[ReasoningExtractor] = None,
        error_detector: Optional[FirstErrorDetector] = None,
        response_interpreter: Optional[ResponseInterpreter] = None,
        session_repository: Optional[SessionRepository] = None,
    ) -> None:
        self.concept_graph = concept_graph
        self.misconception_library = misconception_library
        self.question_selector = question_selector
        self.bayesian_engine = bayesian_engine or BayesianEngine()
        self.reasoning_extractor = reasoning_extractor or ReasoningExtractor(
            provider=MockLLMProvider(),
            concept_graph=concept_graph,
        )
        self.error_detector = error_detector or FirstErrorDetector(
            misconception_library=misconception_library,
            concept_graph=concept_graph,
        )
        self.response_interpreter = response_interpreter or MockResponseInterpreter()
        self.session_repository = session_repository or SQLiteSessionRepository()

    @classmethod
    def create_default(
        cls,
        data_dir: Optional[Path] = None,
        llm_provider: Optional[LLMProvider] = None,
        db_path: Optional[str] = None,
    ) -> "DiagnosisService":
        """Instantiate DiagnosisService with standard default JSON catalog files."""
        base_dir = data_dir or Path("data")
        concepts_path = base_dir / "concepts" / "physics_force_motion.json"
        misconceptions_path = base_dir / "misconceptions" / "physics_force_motion.json"
        likelihoods_path = base_dir / "misconceptions" / "likelihoods.json"
        default_db = str(base_dir / "mindtrace_sessions.db")
        chosen_db = db_path if db_path is not None else default_db

        cg = ConceptGraph.load_from_json(concepts_path)
        ml = MisconceptionLibrary.load_from_json(misconceptions_path, concept_graph=cg)
        qs = ActiveQuestionSelector.load_from_json(likelihoods_path)
        re = ReasoningExtractor(provider=llm_provider or SmartOfflineLLMProvider(), concept_graph=cg)
        ed = FirstErrorDetector(misconception_library=ml, concept_graph=cg)
        repo = SQLiteSessionRepository(db_path=chosen_db)

        return cls(
            concept_graph=cg,
            misconception_library=ml,
            question_selector=qs,
            reasoning_extractor=re,
            error_detector=ed,
            session_repository=repo,
        )

    def submit_diagnosis(self, request: DiagnosisSubmitRequest) -> DiagnosisSubmitResponse:
        """
        End-to-end processing of an initial student reasoning submission.
        """
        session_id = f"diag_{uuid.uuid4().hex[:10]}"

        # 1. Extract structured reasoning
        extracted = self.reasoning_extractor.extract_reasoning(
            question=request.question_text,
            student_response=request.student_response,
            question_id=request.question_id,
            context_concepts=request.relevant_concept_ids,
        )

        # 2. Evaluate reasoning steps and identify first error
        first_error = self.error_detector.evaluate(extracted, request.rubric)

        # 3. Retrieve prerequisite repair path from ConceptGraph
        prereqs_to_review: List[str] = []
        first_err_concept: Optional[str] = None
        if first_error.first_error_step_id is not None:
            # Find the concept associated with the first error step
            for se in first_error.step_evaluations:
                if se.student_step_id == first_error.first_error_step_id:
                    if se.affected_concepts:
                        first_err_concept = se.affected_concepts[0]
                        # Trace upstream prerequisites from concept graph
                        all_prereqs = self.concept_graph.get_all_prerequisites(first_err_concept)
                        prereqs_to_review = all_prereqs
                    break

        # 4. Initialize Bayesian diagnostic session
        candidates = list(first_error.candidate_misconception_ids)
        if not candidates:
            candidates = ["unknown_or_other"]

        diag_session = self.bayesian_engine.initialize_session(
            session_id=session_id,
            candidate_hypotheses=candidates,
            include_unknown=True,
        )

        # 5. Select follow-up question if an error was detected
        followup_view: Optional[FollowupQuestionView] = None
        if first_error.first_error_step_id is not None:
            best_q, ig, rationale = self.question_selector.select_best_question(diag_session)
            if best_q is not None:
                followup_view = FollowupQuestionView(
                    question_id=best_q.question_id,
                    question_text=best_q.question_text,
                    expected_information_gain=ig,
                    selection_rationale=rationale,
                    calibration_status=best_q.calibration_status,
                )

        # Set status
        if first_error.first_error_step_id is None:
            status = "sufficient_evidence" if extracted.extraction_status == "complete" else "inconclusive"
        elif followup_view is None:
            status = "no_available_questions"
        else:
            status = "collecting_evidence"

        diag_session.session_status = status

        # 6. Persist session
        session_record = {
            "session_id": session_id,
            "student_id": request.student_id,
            "question_id": request.question_id,
            "original_question": request.question_text,
            "original_student_response": request.student_response,
            "extracted_reasoning": extracted.model_dump(),
            "first_error_result": first_error.model_dump(),
            "diagnostic_session": diag_session.model_dump(),
            "prerequisite_concepts_to_review": prereqs_to_review,
            "diagnostic_status": status,
        }
        self.session_repository.save_session(session_record)

        posterior_dist = {
            h: b.posterior_probability for h, b in diag_session.hypothesis_beliefs.items()
        }

        return DiagnosisSubmitResponse(
            diagnosis_session_id=session_id,
            student_id=request.student_id,
            question_id=request.question_id,
            extracted_reasoning=extracted,
            first_error_result=first_error,
            candidate_misconception_ids=first_error.candidate_misconception_ids,
            posterior_hypothesis_distribution=posterior_dist,
            selected_followup_question=followup_view,
            diagnostic_status=status,
            prerequisite_concepts_to_review=prereqs_to_review,
            uncertainty_notes=first_error.uncertainty_notes,
            calibration_status="illustrative",
        )

    def process_followup(self, request: DiagnosisFollowupRequest) -> DiagnosisFollowupResponse:
        """
        Process student's response to an active diagnostic follow-up probe.
        """
        session_record = self.session_repository.get_session(request.diagnosis_session_id)
        if session_record is None:
            raise KeyError(f"Diagnostic session '{request.diagnosis_session_id}' not found.")

        diag_session = DiagnosticSession.model_validate(session_record["diagnostic_session"])

        # Check for repeated question
        if request.followup_question_id in diag_session.asked_question_ids:
            raise ValueError(
                f"Question '{request.followup_question_id}' has already been answered in this session."
            )

        # Locate question model
        q_model: Optional[DiagnosticQuestionModel] = None
        for q in self.question_selector.question_catalog:
            if q.question_id == request.followup_question_id:
                q_model = q
                break

        if q_model is None:
            # Fallback for dynamic / uncataloged question probe
            q_model = DiagnosticQuestionModel(
                question_id=request.followup_question_id,
                question_text="Uncataloged diagnostic probe",
                target_hypotheses=diag_session.candidate_hypotheses,
                response_likelihoods={},
                calibration_status="illustrative",
            )

        # Interpret response into structured evidence observation
        seq_num = len(diag_session.evidence_history) + 1
        obs = self.response_interpreter.interpret(
            question=q_model,
            student_response=request.student_response,
            sequence_number=seq_num,
        )

        # Execute Bayesian update
        update_result = self.bayesian_engine.update(
            session=diag_session,
            observation=obs,
            question_likelihoods=q_model.response_likelihoods,
        )

        # Select next follow-up question if more evidence is needed
        next_followup_view: Optional[FollowupQuestionView] = None
        if diag_session.session_status == "collecting_evidence":
            next_q, next_ig, next_rationale = self.question_selector.select_best_question(diag_session)
            if next_q is not None:
                next_followup_view = FollowupQuestionView(
                    question_id=next_q.question_id,
                    question_text=next_q.question_text,
                    expected_information_gain=next_ig,
                    selection_rationale=next_rationale,
                    calibration_status=next_q.calibration_status,
                )
            else:
                diag_session.session_status = "no_available_questions"

        # Update persisted session
        session_record["diagnostic_session"] = diag_session.model_dump()
        session_record["diagnostic_status"] = diag_session.session_status
        self.session_repository.save_session(session_record)

        return DiagnosisFollowupResponse(
            diagnosis_session_id=request.diagnosis_session_id,
            interpreted_evidence=obs,
            updated_hypothesis_distribution=update_result.posterior_distribution,
            evidence_history_count=len(diag_session.evidence_history),
            diagnostic_status=diag_session.session_status,
            next_followup_question=next_followup_view,
            uncertainty_notes=update_result.uncertainty_notes,
            calibration_status="illustrative",
        )

    def get_concepts(self) -> ConceptListResponse:
        """Retrieve the entire prerequisite concept graph topology."""
        concept_ids = self.concept_graph.get_all_concepts()
        views: List[ConceptDetailView] = []

        for cid in sorted(concept_ids):
            data = self.concept_graph.get_concept(cid)
            prereqs = self.concept_graph.get_direct_prerequisites(cid)
            related = self.concept_graph.get_related_concepts(cid)
            views.append(
                ConceptDetailView(
                    id=cid,
                    name=data.get("name", cid),
                    topic=data.get("topic", ""),
                    description=data.get("description", ""),
                    prerequisites=prereqs,
                    related_concepts=related,
                )
            )

        stats = self.concept_graph.get_graph_statistics()
        return ConceptListResponse(
            subject=self.concept_graph.graph_data.subject,
            domain=self.concept_graph.graph_data.domain,
            version=self.concept_graph.graph_data.version,
            total_concepts=stats["concept_nodes"],
            total_prerequisite_edges=stats["prerequisite_edges"],
            concepts=views,
        )

    def export_for_member_2(self, session_id: str) -> Member2DiagnosisExport:
        """
        Generate the clean diagnosis output contract for Member 2's adaptive learning engine.
        """
        session_record = self.session_repository.get_session(session_id)
        if session_record is None:
            raise KeyError(f"Session '{session_id}' not found.")

        first_error = session_record["first_error_result"]
        diag_session = session_record["diagnostic_session"]

        posteriors = {
            h: belief["posterior_probability"]
            for h, belief in diag_session["hypothesis_beliefs"].items()
        }

        # Calculate evidence confidence
        evidence_count = len(diag_session.get("evidence_history", []))
        confidence = min(1.0, 0.4 + (0.3 * evidence_count))

        first_err_concept = None
        first_err_order = first_error.get("first_error_order")
        identified_cat = first_error.get("error_type")

        for se in first_error.get("step_evaluations", []):
            if se.get("student_step_id") == first_error.get("first_error_step_id"):
                if se.get("affected_concepts"):
                    first_err_concept = se["affected_concepts"][0]
                break

        return Member2DiagnosisExport(
            student_id=session_record["student_id"],
            session_id=session_id,
            question_id=session_record["question_id"],
            relevant_concept_ids=first_error.get("candidate_misconception_ids", []),
            first_error_concept_id=first_err_concept,
            first_error_step_order=first_err_order,
            identified_error_category=identified_cat,
            candidate_misconception_ids=first_error.get("candidate_misconception_ids", []),
            posterior_hypotheses=posteriors,
            diagnostic_status=diag_session.get("session_status", "inconclusive"),
            prerequisite_concepts_to_review=session_record.get("prerequisite_concepts_to_review", []),
            evidence_confidence=confidence,
        )
