import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from backend.app.adaptive_learning.assessment_schemas import (
    QuestionDifficulty,
    QuestionModel,
    QuestionType,
)
from backend.app.diagnosis.concept_graph import ConceptGraph


class QuestionBank:
    """
    Catalog and index of assessment and diagnostic questions mapped to the
    Physics prerequisite concept graph and misconception library.
    """

    def __init__(
        self,
        questions: Optional[List[QuestionModel]] = None,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> None:
        self._questions: Dict[str, QuestionModel] = {}
        self._by_concept: Dict[str, List[QuestionModel]] = {}
        self._by_difficulty: Dict[QuestionDifficulty, List[QuestionModel]] = {
            QuestionDifficulty.EASY: [],
            QuestionDifficulty.MEDIUM: [],
            QuestionDifficulty.HARD: [],
        }
        self.concept_graph = concept_graph

        if questions:
            for q in questions:
                self.add_question(q)

    def add_question(self, question: QuestionModel) -> None:
        """Register a question in the internal indices."""
        self._questions[question.id] = question
        self._by_concept.setdefault(question.concept_id, []).append(question)
        for sec in question.secondary_concept_ids:
            self._by_concept.setdefault(sec, []).append(question)
        self._by_difficulty[question.difficulty].append(question)

    def get_question(self, question_id: str) -> Optional[QuestionModel]:
        """Lookup question by unique identifier."""
        return self._questions.get(question_id)

    def get_all_questions(self) -> List[QuestionModel]:
        """Return all cataloged questions."""
        return list(self._questions.values())

    def get_questions_by_concept(
        self,
        concept_id: str,
        difficulty: Optional[QuestionDifficulty] = None,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[QuestionModel]:
        """
        Retrieve questions mapped to a concept, optionally filtered by difficulty
        and excluding previously answered question IDs.
        """
        exclude = set(exclude_ids or [])
        candidates = self._by_concept.get(concept_id, [])

        results: List[QuestionModel] = []
        for q in candidates:
            if q.id in exclude:
                continue
            if difficulty is not None and q.difficulty != difficulty:
                continue
            if q not in results:
                results.append(q)

        return results

    def evaluate_answer(
        self,
        question_id: str,
        student_answer: str,
    ) -> Tuple[bool, float, str]:
        """
        Evaluate a student answer against the registered question rubric and answer key.
        Returns: (is_correct, score [0.0..1.0], feedback_text)
        """
        question = self.get_question(question_id)
        if question is None:
            raise KeyError(f"Question '{question_id}' not found in QuestionBank.")

        cleaned_student = student_answer.strip()
        cleaned_correct = question.correct_answer.strip()

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Check letter match (e.g. 'B' or 'B)' or 'Option B')
            is_correct = self._evaluate_mcq(cleaned_student, cleaned_correct, question.options)
            score = 1.0 if is_correct else 0.0
            feedback = (
                f"Correct! {question.rubric}"
                if is_correct
                else f"Incorrect. Correct answer is ({cleaned_correct}). {question.rubric}"
            )
            return is_correct, score, feedback

        elif question.question_type == QuestionType.NUMERICAL:
            is_correct = self._evaluate_numerical(cleaned_student, cleaned_correct)
            score = 1.0 if is_correct else 0.0
            feedback = (
                f"Correct numerical calculation! {question.rubric}"
                if is_correct
                else f"Incorrect calculation. Expected {cleaned_correct}. {question.rubric}"
            )
            return is_correct, score, feedback

        else:
            # Conceptual / text response matching
            is_correct = cleaned_student.lower() == cleaned_correct.lower()
            score = 1.0 if is_correct else 0.0
            feedback = question.rubric
            return is_correct, score, feedback

    def _evaluate_mcq(self, student_ans: str, correct_key: str, options: List[str]) -> bool:
        """Handle robust MCQ matching: letter, option text, or prefix."""
        # 1. Direct letter match (case-insensitive)
        first_char = student_ans[:1].upper()
        if first_char == correct_key.upper():
            return True

        # 2. Check if student answered with the full option text
        target_option_text = ""
        for opt in options:
            if opt.strip().upper().startswith(correct_key.upper()):
                target_option_text = opt
                break

        if target_option_text:
            opt_body = re.sub(r"^[A-Z][\)\.\:\-]\s*", "", target_option_text, flags=re.IGNORECASE).strip().lower()
            cleaned_ans = student_ans.strip().lower()
            if opt_body and (cleaned_ans == opt_body or opt_body in cleaned_ans or cleaned_ans in opt_body):
                return True

        return False

    def _evaluate_numerical(self, student_ans: str, correct_ans: str) -> bool:
        """Evaluate numerical inputs allowing minor rounding tolerance."""
        try:
            # Extract first floating point number
            student_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", student_ans)
            correct_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", correct_ans)

            if not student_match or not correct_match:
                return student_ans.strip().lower() == correct_ans.strip().lower()

            s_val = float(student_match.group(0))
            c_val = float(correct_match.group(0))

            if abs(c_val) < 1e-6:
                return abs(s_val) < 1e-4

            # 3% relative tolerance
            return abs(s_val - c_val) / abs(c_val) <= 0.03

        except (ValueError, ZeroDivisionError):
            return student_ans.strip().lower() == correct_ans.strip().lower()

    @classmethod
    def load_from_json(
        cls,
        json_path: Path | str,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> "QuestionBank":
        """Factory loading question bank from JSON file."""
        path = Path(json_path)
        if not path.is_file():
            raise FileNotFoundError(f"Question file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_questions = data.get("questions", [])
        parsed = [QuestionModel.model_validate(q) for q in raw_questions]
        return cls(questions=parsed, concept_graph=concept_graph)
