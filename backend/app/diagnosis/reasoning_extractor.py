from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, List, Optional

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.reasoning_schemas import (
    ExtractedReasoning,
    ReasoningStep,
)


class LLMProvider(ABC):
    """Abstract interface for LLM providers generating structured output."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response text for the given prompt."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider for offline tests and decoupled execution.
    Matches substrings in the prompt to return predefined JSON outputs.
    """

    def __init__(
        self,
        canned_responses: Optional[Dict[str, str]] = None,
        default_response: Optional[str] = None,
    ) -> None:
        self.canned_responses: Dict[str, str] = canned_responses or {}
        self.default_response: str = default_response or "{}"

    def register_response(self, keyword: str, json_response: str) -> None:
        """Register a canned response triggered when keyword appears in prompt."""
        self.canned_responses[keyword] = json_response

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        for keyword, response in self.canned_responses.items():
            if keyword in prompt:
                return response
        return self.default_response


class FailingLLMProvider(LLMProvider):
    """Mock provider that simulates API timeouts or network failure."""

    def __init__(self, error_message: str = "Provider connection timed out") -> None:
        self.error_message = error_message

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise RuntimeError(self.error_message)


class ReasoningExtractor:
    """
    Extracts structured, ordered reasoning evidence from open-ended student responses.
    
    Transforms natural-language answers into verified ExtractedReasoning objects,
    enforcing evidence traceability and referential integrity against ConceptGraph.
    """

    SYSTEM_PROMPT = (
        "You are an expert Physics Reasoning Diagnosis Assistant for MINDTRACE. "
        "Your task is to extract structured, chronological reasoning evidence from "
        "a student's explanation without altering their words or inventing unstated assumptions. "
        "Return strictly valid JSON conforming to the requested schema."
    )

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> None:
        self.provider = provider or MockLLMProvider()
        self.concept_graph = concept_graph

    def build_prompt(
        self,
        question: str,
        student_response: str,
        question_id: str,
        context_concepts: Optional[List[str]] = None,
    ) -> str:
        """Construct the extraction prompt with context constraints."""
        concept_context_str = ""
        if context_concepts:
            concept_context_str = f"\nRelevant Concept Context: {', '.join(context_concepts)}"
        elif self.concept_graph:
            concept_context_str = f"\nAvailable Concepts: {', '.join(self.concept_graph.get_all_concepts())}"

        return (
            f"Question ID: {question_id}\n"
            f"Question: {question}\n"
            f"Student Response: \"{student_response}\"{concept_context_str}\n\n"
            "Extract the reasoning steps following these rules:\n"
            "1. Extract ONLY what the student explicitly asserted.\n"
            "2. Keep evidence_text an EXACT verbatim substring from the student response.\n"
            "3. Number steps sequentially starting from order: 1.\n"
            "4. Classify each step reasoning_type from: factual_claim, conceptual_assumption, "
            "formula_selection, mathematical_operation, inference, conclusion, unknown.\n"
            "5. If reasoning is incomplete or ambiguous, set extraction_status to 'partial' "
            "or 'insufficient_information'.\n"
            "Output JSON format:\n"
            "{\n"
            '  "question_id": "...",\n'
            '  "original_student_response": "...",\n'
            '  "reasoning_steps": [\n'
            '    {\n'
            '      "step_id": "step_1",\n'
            '      "order": 1,\n'
            '      "original_text": "...",\n'
            '      "claim": "...",\n'
            '      "reasoning_type": "...",\n'
            '      "concept_ids": ["..."],\n'
            '      "formulas": ["..."],\n'
            '      "inference": "...",\n'
            '      "evidence_text": "...",\n'
            '      "uncertainty_flag": false\n'
            '    }\n'
            '  ],\n'
            '  "identified_concepts": ["..."],\n'
            '  "extraction_status": "complete|partial|insufficient_information",\n'
            '  "ambiguity_notes": ["..."]\n'
            "}"
        )

    def validate_concepts(self, extracted: ExtractedReasoning) -> bool:
        """
        Verify that all concepts in identified_concepts and reasoning steps exist
        within the associated ConceptGraph.
        """
        if self.concept_graph is None:
            return True

        known_concepts = set(self.concept_graph.get_all_concepts())
        for concept_id in extracted.identified_concepts:
            if concept_id not in known_concepts:
                raise InvalidConceptReferenceError(
                    f"Unknown concept ID '{concept_id}' in identified_concepts."
                )

        for step in extracted.reasoning_steps:
            for concept_id in step.concept_ids:
                if concept_id not in known_concepts:
                    raise InvalidConceptReferenceError(
                        f"Unknown concept ID '{concept_id}' referenced in step '{step.step_id}'."
                    )
        return True

    def _clean_json_output(self, raw_text: str) -> str:
        """Strip markdown code fence blocks if returned by LLM."""
        text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    def extract_reasoning(
        self,
        question: str,
        student_response: str,
        question_id: str = "Q001",
        context_concepts: Optional[List[str]] = None,
        strict_concepts: bool = True,
        strict_validation: bool = False,
    ) -> ExtractedReasoning:
        """
        Extract structured reasoning evidence from a student response.
        
        Handles malformed outputs, empty responses, and provider failures safely.
        """
        # Rule: Empty or non-informative student responses must not produce fabricated steps
        trimmed_response = student_response.strip()
        if not trimmed_response or len(trimmed_response) < 3:
            return ExtractedReasoning(
                question_id=question_id,
                original_student_response=student_response,
                reasoning_steps=[],
                identified_concepts=[],
                extraction_status="insufficient_information",
                ambiguity_notes=["Student response is empty or insufficient to extract reasoning."],
            )

        prompt = self.build_prompt(
            question=question,
            student_response=student_response,
            question_id=question_id,
            context_concepts=context_concepts,
        )

        try:
            raw_output = self.provider.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
            )
        except Exception as e:
            if strict_validation:
                raise
            return ExtractedReasoning(
                question_id=question_id,
                original_student_response=student_response,
                reasoning_steps=[],
                identified_concepts=[],
                extraction_status="insufficient_information",
                ambiguity_notes=[f"LLM provider error: {str(e)}"],
            )

        cleaned_json = self._clean_json_output(raw_output)

        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            if strict_validation:
                raise
            return ExtractedReasoning(
                question_id=question_id,
                original_student_response=student_response,
                reasoning_steps=[],
                identified_concepts=[],
                extraction_status="insufficient_information",
                ambiguity_notes=[f"Malformed JSON from LLM provider: {str(e)}"],
            )

        # Enforce original_student_response in parsed data matches incoming input
        parsed_data["original_student_response"] = student_response
        parsed_data["question_id"] = question_id

        try:
            extracted = ExtractedReasoning.model_validate(parsed_data)
        except Exception as e:
            if strict_validation:
                raise
            return ExtractedReasoning(
                question_id=question_id,
                original_student_response=student_response,
                reasoning_steps=[],
                identified_concepts=[],
                extraction_status="insufficient_information",
                ambiguity_notes=[f"Validation error in structured extraction: {str(e)}"],
            )

        # Validate concept references against ConceptGraph if present
        if self.concept_graph is not None and strict_concepts:
            self.validate_concepts(extracted)

        return extracted
