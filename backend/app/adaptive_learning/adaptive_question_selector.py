from typing import List, Optional

from backend.app.adaptive_learning.assessment_schemas import (
    AdaptiveNextQuestionResponse,
    QuestionDifficulty,
    QuestionModel,
)
from backend.app.adaptive_learning.difficulty_engine import AdaptiveDifficultyEngine
from backend.app.adaptive_learning.learner_model import LearnerModel
from backend.app.adaptive_learning.question_bank import QuestionBank
from backend.app.diagnosis.concept_graph import ConceptGraph


class AdaptiveQuestionSelector:
    """
    Orchestrates prerequisite checking, learner mastery lookup, and difficulty adaptation
    to select the single next best question for a student.
    """

    def __init__(
        self,
        question_bank: QuestionBank,
        concept_graph: ConceptGraph,
        learner_model: LearnerModel,
        difficulty_engine: Optional[AdaptiveDifficultyEngine] = None,
        prerequisite_threshold: float = 0.45,
    ) -> None:
        self.question_bank = question_bank
        self.concept_graph = concept_graph
        self.learner_model = learner_model
        self.difficulty_engine = difficulty_engine or AdaptiveDifficultyEngine()
        self.prerequisite_threshold = prerequisite_threshold

    def select_next_question(
        self,
        student_id: str,
        target_concept_id: Optional[str] = None,
        exclude_question_ids: Optional[List[str]] = None,
        allow_prerequisite_diversion: bool = True,
    ) -> AdaptiveNextQuestionResponse:
        """
        Identify next question by verifying prerequisite readiness and adapting difficulty.
        """
        exclude = list(exclude_question_ids or [])
        profile = self.learner_model.get_or_create_profile(student_id)

        # 1. Determine target concept if not provided
        if not target_concept_id:
            target_concept_id = self._pick_default_target_concept(student_id)

        current_mastery = self.learner_model.get_concept_mastery(student_id, target_concept_id)

        # 2. Check prerequisites via Concept Graph
        prereq_blocked = False
        blocker_concept_id: Optional[str] = None
        actual_concept_to_test = target_concept_id

        if allow_prerequisite_diversion:
            direct_prereqs = self.concept_graph.get_direct_prerequisites(target_concept_id)
            weakest_prereq: Optional[str] = None
            lowest_prereq_mastery = 1.0

            for p_id in direct_prereqs:
                p_mastery = self.learner_model.get_concept_mastery(student_id, p_id)
                if p_mastery < self.prerequisite_threshold and p_mastery < lowest_prereq_mastery:
                    lowest_prereq_mastery = p_mastery
                    weakest_prereq = p_id

            if weakest_prereq is not None:
                prereq_blocked = True
                blocker_concept_id = weakest_prereq
                actual_concept_to_test = weakest_prereq

        # 3. Determine difficulty for the chosen concept
        effective_mastery = self.learner_model.get_concept_mastery(student_id, actual_concept_to_test)
        rec_diff, diff_rationale = self.difficulty_engine.determine_difficulty(effective_mastery)

        # 4. Fetch candidate questions
        selected_q = self._find_best_matching_question(
            concept_id=actual_concept_to_test,
            preferred_difficulty=rec_diff,
            exclude_ids=exclude,
        )

        # 5. Formulate human-readable pedagogical reason
        if prereq_blocked and blocker_concept_id:
            reason = (
                f"Prerequisite gap detected: '{blocker_concept_id}' mastery is only {effective_mastery:.2f} "
                f"(below threshold {self.prerequisite_threshold:.2f}). Recommending foundational question on "
                f"'{blocker_concept_id}' before proceeding to '{target_concept_id}'."
            )
        else:
            reason = (
                f"Targeting concept '{target_concept_id}' (Mastery: {effective_mastery:.2f}). {diff_rationale}"
            )

        if selected_q is None:
            reason += " (Note: All registered questions for this concept/difficulty have been exhausted)."

        return AdaptiveNextQuestionResponse(
            question=selected_q,
            target_concept_id=target_concept_id,
            actual_question_concept_id=actual_concept_to_test,
            recommended_difficulty=rec_diff,
            selection_reason=reason,
            prerequisite_blocked=prereq_blocked,
            prerequisite_concept_id=blocker_concept_id,
            current_concept_mastery=round(effective_mastery, 4),
            overall_proficiency=profile.overall_proficiency,
        )

    def _pick_default_target_concept(self, student_id: str) -> str:
        """Pick the lowest mastery concept or fall back to topological root."""
        masteries = self.learner_model.get_all_masteries(student_id)
        if masteries:
            # Sort ascending by mastery
            sorted_concepts = sorted(masteries.items(), key=lambda kv: kv[1])
            return sorted_concepts[0][0]

        learning_order = self.concept_graph.get_learning_order()
        return learning_order[0] if learning_order else "force"

    def _find_best_matching_question(
        self,
        concept_id: str,
        preferred_difficulty: QuestionDifficulty,
        exclude_ids: List[str],
    ) -> Optional[QuestionModel]:
        """Search for question with fallback to other difficulties if preferred is exhausted."""
        # First attempt: preferred difficulty
        candidates = self.question_bank.get_questions_by_concept(
            concept_id=concept_id,
            difficulty=preferred_difficulty,
            exclude_ids=exclude_ids,
        )
        if candidates:
            return candidates[0]

        # Second attempt: any difficulty for this concept
        any_diff = self.question_bank.get_questions_by_concept(
            concept_id=concept_id,
            difficulty=None,
            exclude_ids=exclude_ids,
        )
        if any_diff:
            return any_diff[0]

        return None
