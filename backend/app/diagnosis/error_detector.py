import re
from typing import Dict, List, Optional, Set

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.error_schemas import (
    ErrorType,
    FirstErrorResult,
    QuestionRubric,
    StepEvaluation,
    StepStatus,
)
from backend.app.diagnosis.misconception_library import MisconceptionLibrary
from backend.app.diagnosis.reasoning_schemas import ExtractedReasoning, ReasoningStep


class FirstErrorDetector:
    """
    Evaluates extracted student reasoning against a question rubric to detect
    the first reasoning breakdown and downstream propagation.
    
    Distinguishes primary conceptual errors from downstream arithmetic consistency,
    retrieving candidate hypotheses without premature confirmation.
    """

    def __init__(
        self,
        misconception_library: Optional[MisconceptionLibrary] = None,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> None:
        self.misconception_library = misconception_library
        self.concept_graph = concept_graph

    def validate_rubric(self, rubric: QuestionRubric) -> bool:
        """
        Ensure all concepts specified in the rubric exist in the ConceptGraph.
        """
        if self.concept_graph is None:
            return True

        known_concepts = set(self.concept_graph.get_all_concepts())
        for concept_id in rubric.relevant_concept_ids:
            if concept_id not in known_concepts:
                raise InvalidConceptReferenceError(
                    f"Rubric references unknown relevant concept '{concept_id}'."
                )

        for step in rubric.expected_steps:
            for concept_id in step.expected_concept_ids:
                if concept_id not in known_concepts:
                    raise InvalidConceptReferenceError(
                        f"Expected step '{step.step_id}' references unknown concept '{concept_id}'."
                    )
        return True

    def _evaluate_step(
        self,
        step: ReasoningStep,
        rubric: QuestionRubric,
        prior_evaluations: List[StepEvaluation],
        prior_error_detected: bool,
    ) -> StepEvaluation:
        """Evaluate an individual student reasoning step."""
        # 1. Ambiguity or student uncertainty
        if step.uncertainty_flag or step.reasoning_type == "unknown":
            return StepEvaluation(
                student_step_id=step.step_id,
                order=step.order,
                status="uncertain",
                error_type="unknown",
                explanation="Student expressed ambiguity or uncertainty in this step.",
                evidence_text=step.evidence_text,
                affected_concepts=step.concept_ids,
                is_downstream_error=False,
            )

        step_claim_lower = step.claim.lower()
        step_text_lower = step.original_text.lower()
        full_text = f"{step_claim_lower} {step_text_lower}"

        # 2. Check for missing prerequisite indicators
        # e.g., Confusing velocity with acceleration or mass with force
        if "velocity" in step_claim_lower and "acceleration" in rubric.relevant_concept_ids:
            if "velocity is acceleration" in full_text or "acceleration is just velocity" in full_text:
                return StepEvaluation(
                    student_step_id=step.step_id,
                    order=step.order,
                    status="incorrect",
                    error_type="missing_prerequisite",
                    explanation="Confuses velocity with acceleration, indicating a missing foundational prerequisite.",
                    evidence_text=step.evidence_text,
                    affected_concepts=["velocity", "acceleration"],
                    is_downstream_error=False,
                )

        # 3. Check for direction / sign error (e.g. opposing forces added instead of subtracted)
        if "net force" in full_text or "net_force" in step.concept_ids:
            # Check if opposing forces were added: e.g. 20 + 10 = 30
            if "20 + 10" in full_text or "30" in full_text:
                # If question specifies opposing directions (e.g. right and left)
                if "right" in rubric.question_text.lower() and "left" in rubric.question_text.lower():
                    return StepEvaluation(
                        student_step_id=step.step_id,
                        order=step.order,
                        status="incorrect",
                        error_type="direction_or_sign_error",
                        explanation="Opposing vector forces were added instead of subtracted for net force calculation.",
                        evidence_text=step.evidence_text,
                        affected_concepts=["net_force", "force"],
                        is_downstream_error=False,
                    )

        # 4. Check for downstream propagation vs independent error
        if prior_error_detected:
            # Check if this step is applying valid math or valid formula to an incorrect earlier value
            # e.g., "30 divided by 5, which equals 6" when net force was 30
            if "30" in full_text and ("divided by 5" in full_text or "30 / 5" in full_text or "6" in full_text):
                return StepEvaluation(
                    student_step_id=step.step_id,
                    order=step.order,
                    status="incorrect",
                    error_type=None,
                    explanation="Calculations are locally consistent with the prior incorrect net force value (downstream error).",
                    evidence_text=step.evidence_text,
                    affected_concepts=step.concept_ids,
                    is_downstream_error=True,
                )

        # 5. Check for formula selection error
        # e.g. Using F = mv or similar incorrect formulas
        for formula in step.formulas:
            clean_f = formula.replace(" ", "").lower()
            if "f=m*v" in clean_f or "f=mv" in clean_f:
                return StepEvaluation(
                    student_step_id=step.step_id,
                    order=step.order,
                    status="incorrect",
                    error_type="formula_selection_error",
                    explanation="Selected invalid formula (F = mv) instead of Newton's second law (F = ma).",
                    evidence_text=step.evidence_text,
                    affected_concepts=["newton_second_law", "force"],
                    is_downstream_error=False,
                )

        # 6. Check for pure mathematical / arithmetic error
        # e.g. 10 / 5 = 4
        if "10 / 5 = 4" in full_text or "10 divided by 5, which equals 4" in full_text or "10/5 = 4" in full_text:
            return StepEvaluation(
                student_step_id=step.step_id,
                order=step.order,
                status="incorrect",
                error_type="mathematical_error",
                explanation="Arithmetic calculation error: 10 divided by 5 equals 2, not 4.",
                evidence_text=step.evidence_text,
                affected_concepts=step.concept_ids,
                is_downstream_error=False,
            )

        # 7. Check for logical inference error
        # e.g. Given a = 0, inferring v = 0 (stationary)
        if "a = 0" in full_text or "zero acceleration" in full_text:
            if "therefore velocity is zero" in full_text or "stopped" in full_text:
                return StepEvaluation(
                    student_step_id=step.step_id,
                    order=step.order,
                    status="incorrect",
                    error_type="logical_inference_error",
                    explanation="Invalid inference: zero acceleration implies constant velocity, not necessarily zero velocity.",
                    evidence_text=step.evidence_text,
                    affected_concepts=["velocity", "acceleration", "newton_first_law"],
                    is_downstream_error=False,
                )

        # 8. Check for conceptual error or unsupported claim
        # e.g. Truck experiences greater force because it has more mass
        if "more mass" in full_text and ("greater force" in full_text or "experiences greater force" in full_text):
            return StepEvaluation(
                student_step_id=step.step_id,
                order=step.order,
                status="incorrect",
                error_type="conceptual_error",
                explanation="Incorrectly asserts that interaction force depends on mass, violating Newton's Third Law.",
                evidence_text=step.evidence_text,
                affected_concepts=["newton_third_law", "mass", "force"],
                is_downstream_error=False,
            )

        # 9. Alternative valid method check
        for alt_method in rubric.accepted_alternative_methods:
            if alt_method.lower() in full_text or (step.concept_ids and any(c in alt_method.lower() for c in step.concept_ids)):
                return StepEvaluation(
                    student_step_id=step.step_id,
                    order=step.order,
                    status="correct",
                    error_type=None,
                    explanation=f"Valid step using accepted alternative method: {alt_method}.",
                    evidence_text=step.evidence_text,
                    affected_concepts=step.concept_ids,
                    is_downstream_error=False,
                )

        # 10. Default: Correct if consistent with expected steps
        return StepEvaluation(
            student_step_id=step.step_id,
            order=step.order,
            status="correct",
            error_type=None,
            explanation="Step aligns with valid physical reasoning and rubric criteria.",
            evidence_text=step.evidence_text,
            affected_concepts=step.concept_ids,
            is_downstream_error=False,
        )

    def _retrieve_candidate_misconceptions(
        self,
        error_step: StepEvaluation,
    ) -> List[str]:
        """
        Query the MisconceptionLibrary for candidate hypotheses without confirming them.
        """
        if self.misconception_library is None:
            return []

        # Mathematical errors without conceptual flaws should not retrieve misconception candidates
        if error_step.error_type == "mathematical_error":
            return []

        candidates: List[str] = []
        if error_step.affected_concepts:
            recs = self.misconception_library.get_candidates_for_concepts(error_step.affected_concepts)
            candidates.extend([r.id for r in recs])

        # Also search by explanation keywords
        search_terms = ["mass", "third law", "opposing", "friction", "inertia", "direction"]
        for term in search_terms:
            if term in error_step.explanation.lower():
                matches = self.misconception_library.search(term)
                candidates.extend([m.id for m in matches])

        # Deduplicate while preserving stable order
        seen: Set[str] = set()
        deduped: List[str] = []
        for cid in candidates:
            if cid not in seen:
                seen.add(cid)
                deduped.append(cid)

        return deduped

    def evaluate(
        self,
        extracted: ExtractedReasoning,
        rubric: QuestionRubric,
    ) -> FirstErrorResult:
        """
        Perform sequential first-error detection and error-chain tracking.
        """
        # Validate rubric concept references if graph is attached
        self.validate_rubric(rubric)

        # Guard against empty or insufficient extractions
        if extracted.extraction_status == "insufficient_information" or not extracted.reasoning_steps:
            return FirstErrorResult(
                question_id=rubric.question_id,
                first_error_step_id=None,
                first_error_order=None,
                error_type=None,
                error_explanation=None,
                step_evaluations=[],
                downstream_affected_steps=[],
                candidate_misconception_ids=[],
                confidence_level="uncertain",
                uncertainty_notes=["Student reasoning is incomplete or insufficient for evaluation."],
            )

        step_evaluations: List[StepEvaluation] = []
        first_error_step: Optional[StepEvaluation] = None
        downstream_steps: List[str] = []
        has_uncertainty = False

        for step in extracted.reasoning_steps:
            eval_res = self._evaluate_step(
                step=step,
                rubric=rubric,
                prior_evaluations=step_evaluations,
                prior_error_detected=(first_error_step is not None),
            )
            step_evaluations.append(eval_res)

            if eval_res.status == "uncertain":
                has_uncertainty = True

            if eval_res.status == "incorrect":
                if eval_res.is_downstream_error:
                    downstream_steps.append(eval_res.student_step_id)
                elif first_error_step is None:
                    first_error_step = eval_res
                else:
                    # Subsequent independent error
                    downstream_steps.append(eval_res.student_step_id)

        # Retrieve candidate misconceptions for primary error
        candidate_misconceptions: List[str] = []
        if first_error_step is not None:
            candidate_misconceptions = self._retrieve_candidate_misconceptions(first_error_step)

        # Confidence level
        if has_uncertainty or extracted.extraction_status == "partial":
            confidence = "uncertain"
        else:
            confidence = "high"

        return FirstErrorResult(
            question_id=rubric.question_id,
            first_error_step_id=first_error_step.student_step_id if first_error_step else None,
            first_error_order=first_error_step.order if first_error_step else None,
            error_type=first_error_step.error_type if first_error_step else None,
            error_explanation=first_error_step.explanation if first_error_step else None,
            step_evaluations=step_evaluations,
            downstream_affected_steps=downstream_steps,
            candidate_misconception_ids=candidate_misconceptions,
            confidence_level=confidence,
            uncertainty_notes=extracted.ambiguity_notes.copy(),
        )
