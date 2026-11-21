from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from backend.app.diagnosis.bayesian_schemas import (
    DiagnosticQuestionModel,
    EvidenceObservation,
    ResponseCategory,
)


class ResponseInterpreter(ABC):
    """Abstract interface for interpreting student natural-language responses."""

    @abstractmethod
    def interpret(
        self,
        question: DiagnosticQuestionModel,
        student_response: str,
        sequence_number: int,
    ) -> EvidenceObservation:
        """Transform student response into a categorized EvidenceObservation."""
        pass


class MockResponseInterpreter(ResponseInterpreter):
    """
    Deterministic mock response interpreter for testing.
    Matches predefined substrings to categorize evidence.
    """

    def __init__(
        self,
        canned_mappings: Optional[Dict[str, ResponseCategory]] = None,
        default_category: ResponseCategory = "neutral_or_inconclusive",
    ) -> None:
        self.canned_mappings = canned_mappings or {}
        self.default_category = default_category

    def register_mapping(self, substring: str, category: ResponseCategory) -> None:
        self.canned_mappings[substring.lower()] = category

    def interpret(
        self,
        question: DiagnosticQuestionModel,
        student_response: str,
        sequence_number: int,
    ) -> EvidenceObservation:
        cleaned = student_response.strip().lower()
        matched_category = self.default_category
        evidence_text = student_response.strip()

        for substring, cat in self.canned_mappings.items():
            if substring in cleaned:
                matched_category = cat
                evidence_text = substring
                break

        return EvidenceObservation(
            question_id=question.question_id,
            original_student_response=student_response,
            response_category=matched_category,
            evidence_text=evidence_text if evidence_text else "unclassified response",
            interpretation_confidence=0.90 if matched_category != "neutral_or_inconclusive" else 0.50,
            sequence_number=sequence_number,
        )
