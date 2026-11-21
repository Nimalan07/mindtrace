from typing import Any, Dict, List, Optional

from backend.app.adaptive_learning.assessment_schemas import QuestionDifficulty, QuestionModel
from backend.app.adaptive_learning.intervention_schemas import (
    InterventionPlan,
    InterventionStage,
    InterventionType,
)
from backend.app.adaptive_learning.question_bank import QuestionBank
from backend.app.diagnosis.concept_graph import ConceptGraph
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.service_schemas import Member2DiagnosisExport


class PersonalizedInterventionEngine:
    """
    Synthesizes targeted instructional remediation plans from Member 1 diagnosis exports.
    Combines prerequisite repair chains, misconception refutation, worked examples,
    and calibrated practice questions.
    """

    def __init__(
        self,
        concept_graph: ConceptGraph,
        misconception_library: MisconceptionLibrary,
        question_bank: QuestionBank,
    ) -> None:
        self.concept_graph = concept_graph
        self.misconception_library = misconception_library
        self.question_bank = question_bank

    def generate_intervention(
        self,
        export: Member2DiagnosisExport,
    ) -> InterventionPlan:
        """
        Generate a comprehensive, actionable intervention plan from Member 1 export.
        """
        target_concept = export.first_error_concept_id or (
            export.relevant_concept_ids[0] if export.relevant_concept_ids else "force"
        )

        # 1. Detect dominant candidate misconception
        dominant_m_id: Optional[str] = None
        dominant_prob = 0.0
        for m_id, prob in export.posterior_hypotheses.items():
            if m_id != "unknown_or_other" and prob > dominant_prob:
                dominant_m_id = m_id
                dominant_prob = prob

        # Filter out if probability is negligible
        if dominant_prob < 0.35:
            dominant_m_id = None
            dominant_prob = 0.0

        misconception_title = None
        misconception_item = None
        if dominant_m_id:
            misconception_item = self.misconception_library.get_by_id(dominant_m_id)
            if misconception_item:
                misconception_title = misconception_item.title

        # 2. Determine intervention type
        prereqs = list(export.prerequisite_concepts_to_review)
        if not prereqs and target_concept:
            # Fallback to direct prerequisites from graph
            prereqs = self.concept_graph.get_direct_prerequisites(target_concept)

        if prereqs and len(prereqs) > 0 and export.identified_error_category in ("conceptual_error", "missing_prerequisite"):
            int_type = InterventionType.PREREQUISITE_REPAIR
        elif dominant_m_id is not None:
            int_type = InterventionType.MISCONCEPTION_REMEDIATION
        elif export.identified_error_category in ("direction_or_sign_error", "calculation_error", "mathematical_error"):
            int_type = InterventionType.PROCEDURAL_CALIBRATION
        else:
            int_type = InterventionType.REINFORCEMENT

        # 3. Build sequential stages
        stages: List[InterventionStage] = []
        stage_num = 1

        # Stage 1: Prerequisite Review (if any identified)
        if prereqs:
            primary_prereq = prereqs[0]
            prereq_details = self.concept_graph.get_concept(primary_prereq)
            prereq_name = prereq_details.get("name", primary_prereq)
            prereq_desc = prereq_details.get("description", "")

            # Look up an easy question for this prerequisite
            prereq_q = self.question_bank.get_questions_by_concept(
                primary_prereq, difficulty=QuestionDifficulty.EASY
            )
            stages.append(
                InterventionStage(
                    stage_order=stage_num,
                    stage_name="Prerequisite Foundation Repair",
                    target_concept=primary_prereq,
                    instructional_content=(
                        f"Before mastering '{target_concept}', let's reinforce prerequisite concept '{prereq_name}': {prereq_desc}"
                    ),
                    suggested_action="Review foundational definitions and complete the warm-up question.",
                    reference_question=prereq_q[0] if prereq_q else None,
                )
            )
            stage_num += 1

        # Stage 2: Conceptual Refutation / Error Remediation
        if misconception_item is not None:
            refutation = (
                f"Clarification regarding '{misconception_item.title}': "
                f"Common misconception: '{misconception_item.incorrect_belief}' "
                f"Scientific reality: {misconception_item.correct_understanding}"
            )
        else:
            refutation = (
                f"Error type observed: {export.identified_error_category or 'reasoning inconsistency'}. "
                f"Take note of direction conventions, signs, and explicit formula conditions for '{target_concept}'."
            )

        stages.append(
            InterventionStage(
                stage_order=stage_num,
                stage_name="Conceptual Remediation & Error Analysis",
                target_concept=target_concept,
                instructional_content=refutation,
                suggested_action="Contrast your reasoning step with the validated physical principles above.",
                reference_question=None,
            )
        )
        stage_num += 1

        # Stage 3: Scaffolded Practice Question
        practice_qs = self.question_bank.get_questions_by_concept(
            target_concept,
            difficulty=QuestionDifficulty.EASY,
            exclude_ids=[export.question_id],
        )
        if not practice_qs:
            practice_qs = self.question_bank.get_questions_by_concept(
                target_concept, difficulty=QuestionDifficulty.MEDIUM, exclude_ids=[export.question_id]
            )

        stages.append(
            InterventionStage(
                stage_order=stage_num,
                stage_name="Guided Practice",
                target_concept=target_concept,
                instructional_content=(
                    f"Now apply the corrected principles to a scaffolded practice problem on '{target_concept}'."
                ),
                suggested_action="Solve the guided question carefully, checking your signs and assumptions.",
                reference_question=practice_qs[0] if practice_qs else None,
            )
        )
        stage_num += 1

        # Stage 4: Mastery Verification Challenge
        challenge_qs = self.question_bank.get_questions_by_concept(
            target_concept,
            difficulty=QuestionDifficulty.HARD,
            exclude_ids=[export.question_id] + ([practice_qs[0].id] if practice_qs else []),
        )
        if not challenge_qs:
            challenge_qs = self.question_bank.get_questions_by_concept(
                target_concept, difficulty=QuestionDifficulty.MEDIUM
            )

        stages.append(
            InterventionStage(
                stage_order=stage_num,
                stage_name="Mastery Verification Challenge",
                target_concept=target_concept,
                instructional_content=(
                    "Solidify your understanding by verifying transfer on this application challenge."
                ),
                suggested_action="Attempt the mastery challenge to confirm the misconception has been resolved.",
                reference_question=challenge_qs[0] if challenge_qs else None,
            )
        )

        # 4. Actionable Summary
        summary = [
            f"Diagnosed error on '{target_concept}' (Category: {export.identified_error_category or 'General'}).",
        ]
        if dominant_m_id:
            summary.append(
                f"Candidate Misconception: {misconception_title or dominant_m_id} (Posterior: {dominant_prob:.1%})."
            )
        if prereqs:
            summary.append(f"Recommended prerequisite review order: {' -> '.join(prereqs)}.")
        summary.append("Work through the 4-stage intervention plan above before retrying the diagnostic task.")

        return InterventionPlan(
            student_id=export.student_id,
            session_id=export.session_id,
            target_concept_id=target_concept,
            intervention_type=int_type,
            identified_misconception_id=dominant_m_id,
            identified_misconception_title=misconception_title,
            misconception_probability=round(dominant_prob, 4),
            diagnostic_confidence=export.evidence_confidence,
            prerequisite_repair_chain=prereqs,
            stages=stages,
            actionable_summary=summary,
        )
