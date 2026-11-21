from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.adaptive_learning.adaptive_question_selector import AdaptiveQuestionSelector
from backend.app.adaptive_learning.adaptive_repository import (
    AdaptiveRepository,
    SQLiteAdaptiveRepository,
)
from backend.app.adaptive_learning.assessment_schemas import (
    AdaptiveNextQuestionRequest,
    AdaptiveNextQuestionResponse,
    AssessmentAnswerRequest,
    AssessmentEvaluation,
    QuestionDifficulty,
)
from backend.app.adaptive_learning.bkt_model import BKTModel
from backend.app.adaptive_learning.difficulty_engine import AdaptiveDifficultyEngine
from backend.app.adaptive_learning.intervention_engine import PersonalizedInterventionEngine
from backend.app.adaptive_learning.intervention_schemas import InterventionPlan
from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.adaptive_learning.question_bank import QuestionBank
from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionCard, SpacedRepetitionEngine
from backend.app.dashboard.dashboard_schemas import (
    StudentAnalyticsResponse,
    TeacherAnalyticsResponse,
)
from backend.app.dashboard.student_analytics import StudentAnalyticsService
from backend.app.dashboard.teacher_analytics import TeacherAnalyticsService
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


class AdaptiveLearningService:
    """
    Unified orchestration service for Member 2 (Adaptive Learning & Assessment).
    Integrates BKT, adaptive difficulty, question selection, personalized interventions,
    spaced repetition scheduling, and student/teacher analytics.
    """

    def __init__(
        self,
        concept_graph: ConceptGraph,
        misconception_library: MisconceptionLibrary,
        question_bank: QuestionBank,
        learner_model: Optional[LearnerModel] = None,
        bkt_model: Optional[BKTModel] = None,
        difficulty_engine: Optional[AdaptiveDifficultyEngine] = None,
        question_selector: Optional[AdaptiveQuestionSelector] = None,
        intervention_engine: Optional[PersonalizedInterventionEngine] = None,
        spaced_repetition: Optional[SpacedRepetitionEngine] = None,
        repository: Optional[AdaptiveRepository] = None,
    ) -> None:
        self.concept_graph = concept_graph
        self.misconception_library = misconception_library
        self.question_bank = question_bank
        self.bkt_model = bkt_model or BKTModel()
        self.learner_model = learner_model or LearnerModel(bkt_model=self.bkt_model)
        self.difficulty_engine = difficulty_engine or AdaptiveDifficultyEngine()
        self.question_selector = question_selector or AdaptiveQuestionSelector(
            question_bank=self.question_bank,
            concept_graph=self.concept_graph,
            learner_model=self.learner_model,
            difficulty_engine=self.difficulty_engine,
        )
        self.intervention_engine = intervention_engine or PersonalizedInterventionEngine(
            concept_graph=self.concept_graph,
            misconception_library=self.misconception_library,
            question_bank=self.question_bank,
        )
        self.spaced_repetition = spaced_repetition or SpacedRepetitionEngine()
        self.repository = repository or SQLiteAdaptiveRepository()

        # Analytics services
        self.student_analytics = StudentAnalyticsService(
            learner_model=self.learner_model,
            concept_graph=self.concept_graph,
            spaced_repetition_engine=self.spaced_repetition,
        )
        self.teacher_analytics = TeacherAnalyticsService(
            learner_model=self.learner_model,
            concept_graph=self.concept_graph,
            misconception_library=self.misconception_library,
        )

    @classmethod
    def create_default(
        cls,
        data_dir: Optional[Path] = None,
        db_path: Optional[str] = None,
    ) -> "AdaptiveLearningService":
        """Factory initializing all engines from standard JSON catalogs and SQLite."""
        base_dir = data_dir or Path("data")
        concepts_path = base_dir / "concepts" / "physics_force_motion.json"
        misconceptions_path = base_dir / "misconceptions" / "physics_force_motion.json"
        questions_path = base_dir / "questions" / "physics_questions.json"
        default_db = str(base_dir / "mindtrace_adaptive.db")
        chosen_db = db_path if db_path is not None else default_db

        cg = ConceptGraph.load_from_json(concepts_path)
        ml = MisconceptionLibrary.load_from_json(misconceptions_path, concept_graph=cg)
        qb = QuestionBank.load_from_json(questions_path, concept_graph=cg)
        repo = SQLiteAdaptiveRepository(db_path=chosen_db)

        service = cls(
            concept_graph=cg,
            misconception_library=ml,
            question_bank=qb,
            repository=repo,
        )

        # Load persisted learner profiles if any exist in the database
        for prof in repo.list_all_profiles():
            service.learner_model._profiles[prof.student_id] = prof

        return service

    def select_next_question(
        self,
        request: AdaptiveNextQuestionRequest,
    ) -> AdaptiveNextQuestionResponse:
        """Adaptive question selection balancing prerequisite gaps and mastery difficulty."""
        return self.question_selector.select_next_question(
            student_id=request.student_id,
            target_concept_id=request.target_concept_id,
            exclude_question_ids=request.exclude_question_ids,
            allow_prerequisite_diversion=request.allow_prerequisite_diversion,
        )

    def submit_assessment_answer(
        self,
        request: AssessmentAnswerRequest,
    ) -> AssessmentEvaluation:
        """
        Evaluate student response, execute BKT mastery update, schedule spaced revision,
        and persist progress.
        """
        question = self.question_bank.get_question(request.question_id)
        if question is None:
            raise KeyError(f"Question '{request.question_id}' not found in question bank.")

        is_correct, score, feedback = self.question_bank.evaluate_answer(
            request.question_id, request.student_answer
        )

        prior_p_l = self.learner_model.get_concept_mastery(request.student_id, question.concept_id)

        # BKT update
        bkt_res = self.learner_model.update_from_assessment(
            student_id=request.student_id,
            concept_id=question.concept_id,
            is_correct=is_correct,
            question_id=request.question_id,
        )

        # Spaced repetition scheduling
        quality_score = 5 if is_correct else 1
        card = self.spaced_repetition.record_review(
            student_id=request.student_id,
            concept_id=question.concept_id,
            quality_score=quality_score,
        )
        self.repository.save_spaced_card(card)

        # Persist updated profile
        profile = self.learner_model.get_or_create_profile(request.student_id)
        self.repository.save_profile(profile)

        # Next difficulty recommendation
        next_diff, _ = self.difficulty_engine.determine_difficulty(bkt_res.updated_mastery)

        # Target misconceptions check
        demonstrated = question.target_misconceptions if not is_correct else []

        return AssessmentEvaluation(
            question_id=request.question_id,
            student_id=request.student_id,
            concept_id=question.concept_id,
            is_correct=is_correct,
            score=score,
            student_answer=request.student_answer,
            correct_answer=question.correct_answer,
            feedback=feedback,
            rubric=question.rubric,
            prior_mastery=prior_p_l,
            updated_mastery=bkt_res.updated_mastery,
            target_misconceptions=question.target_misconceptions,
            demonstrated_misconceptions=demonstrated,
            next_recommended_difficulty=next_diff,
        )

    def generate_intervention(
        self,
        export: Member2DiagnosisExport,
    ) -> InterventionPlan:
        """
        Generate personalized intervention from Member 1's diagnostic export contract,
        updating BKT learner mastery using explicit diagnostic calibration.
        """
        # 1. Update BKT mastery using calibrated likelihood mapping
        self.learner_model.update_from_diagnosis_export(export)
        profile = self.learner_model.get_or_create_profile(export.student_id)
        self.repository.save_profile(profile)

        # 2. Schedule spaced repetition for target and prerequisite concepts
        target_concept = export.first_error_concept_id or (
            export.relevant_concept_ids[0] if export.relevant_concept_ids else "force"
        )
        t_card = self.spaced_repetition.schedule_initial_card(export.student_id, target_concept)
        self.repository.save_spaced_card(t_card)

        for p_id in export.prerequisite_concepts_to_review:
            p_card = self.spaced_repetition.schedule_initial_card(export.student_id, p_id)
            self.repository.save_spaced_card(p_card)

        # 3. Synthesize comprehensive intervention plan
        plan = self.intervention_engine.generate_intervention(export)
        self.repository.save_intervention(plan)
        return plan

    def get_due_spaced_repetition(
        self,
        student_id: str,
    ) -> List[SpacedRepetitionCard]:
        """Fetch all memory retention review cards currently due for a learner."""
        return self.spaced_repetition.get_due_cards(student_id)

    def record_spaced_repetition_review(
        self,
        student_id: str,
        concept_id: str,
        quality_score: int,
    ) -> SpacedRepetitionCard:
        """Update review card after spaced repetition retrieval practice."""
        card = self.spaced_repetition.record_review(
            student_id=student_id,
            concept_id=concept_id,
            quality_score=quality_score,
        )
        self.repository.save_spaced_card(card)
        return card

    def get_student_analytics(self, student_id: str) -> StudentAnalyticsResponse:
        """Retrieve personalized student dashboard analytics."""
        return self.student_analytics.get_student_dashboard(student_id)

    def get_teacher_analytics(self) -> TeacherAnalyticsResponse:
        """Retrieve class-level teacher dashboard analytics."""
        return self.teacher_analytics.get_teacher_dashboard()
