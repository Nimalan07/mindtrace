from collections import defaultdict
import json
from pathlib import Path
from typing import List, Optional, Union

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.misconception_schemas import (
    MisconceptionCatalogData,
    MisconceptionRecord,
)


class MisconceptionNotFoundError(KeyError):
    """Raised when a requested misconception ID does not exist."""

    pass


class MisconceptionLibrary:
    """
    Generic, subject-independent catalog of expert-authored candidate misconceptions.
    
    Provides efficient indexed lookups, multi-concept hypothesis candidate retrieval,
    and keyword/symptom searches across student reasoning indicators.
    """

    def __init__(
        self,
        catalog_data: MisconceptionCatalogData,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> None:
        self.catalog_data = catalog_data
        self._by_id: dict[str, MisconceptionRecord] = {}
        self._by_concept: dict[str, list[MisconceptionRecord]] = defaultdict(list)
        self._build_indexes()

        if concept_graph is not None:
            self.validate_against_graph(concept_graph)

    def _build_indexes(self) -> None:
        """Populate dictionary indexes for O(1) ID and concept lookups."""
        for misconception in self.catalog_data.misconceptions:
            self._by_id[misconception.id] = misconception
            for concept_id in misconception.associated_concepts:
                self._by_concept[concept_id].append(misconception)

    @classmethod
    def load_from_json(
        cls,
        file_path: Union[str, Path],
        concept_graph: Optional[ConceptGraph] = None,
    ) -> "MisconceptionLibrary":
        """Load, validate, and instantiate a MisconceptionLibrary from a JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Misconception catalog file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        catalog_data = MisconceptionCatalogData.model_validate(raw_data)
        return cls(catalog_data, concept_graph=concept_graph)

    def validate_against_graph(self, concept_graph: ConceptGraph) -> bool:
        """
        Verify that all associated concepts exist within the provided ConceptGraph.
        Raises InvalidConceptReferenceError if any unreferenced concept is encountered.
        """
        known_concepts = set(concept_graph.get_all_concepts())
        for misconception in self.catalog_data.misconceptions:
            for concept_id in misconception.associated_concepts:
                if concept_id not in known_concepts:
                    raise InvalidConceptReferenceError(
                        f"Misconception '{misconception.id}' references unknown "
                        f"concept '{concept_id}' in concept graph."
                    )
        return True

    def get_by_id(self, misconception_id: str) -> MisconceptionRecord:
        """Return the misconception record by its unique ID."""
        if misconception_id not in self._by_id:
            raise MisconceptionNotFoundError(
                f"Unknown misconception ID: '{misconception_id}'"
            )
        return self._by_id[misconception_id]

    def get_by_concept(self, concept_id: str) -> List[MisconceptionRecord]:
        """Return all candidate misconceptions associated with a specific concept ID."""
        return list(self._by_concept.get(concept_id, []))

    def search(self, query: str) -> List[MisconceptionRecord]:
        """
        Case-insensitive search across titles, incorrect beliefs, typical reasoning,
        common symptoms, and possible causes.
        """
        clean_query = query.strip().lower()
        if not clean_query:
            return []

        results: list[MisconceptionRecord] = []
        for record in self.catalog_data.misconceptions:
            searchable_text = " ".join([
                record.title,
                record.incorrect_belief,
                " ".join(record.typical_reasoning),
                " ".join(record.common_symptoms),
                " ".join(record.possible_causes),
            ]).lower()

            if clean_query in searchable_text:
                results.append(record)

        return results

    def get_candidates_for_concepts(
        self, concept_ids: List[str]
    ) -> List[MisconceptionRecord]:
        """
        Retrieve candidate misconception hypotheses for a list of target/weak concepts.
        Ranked deterministically by relevance (number of concept matches descending),
        avoiding duplicate records.
        """
        matched_counts: dict[str, int] = defaultdict(int)
        for concept_id in concept_ids:
            for record in self._by_concept.get(concept_id, []):
                matched_counts[record.id] += 1

        if not matched_counts:
            return []

        # Sort by match frequency (descending), then by ID (alphabetical) for stability
        sorted_ids = sorted(
            matched_counts.keys(),
            key=lambda mid: (-matched_counts[mid], mid),
        )
        return [self._by_id[mid] for mid in sorted_ids]

    def get_all_misconceptions(self) -> List[MisconceptionRecord]:
        """Return all expert-authored candidate misconceptions in the catalog."""
        return list(self.catalog_data.misconceptions)

    def __len__(self) -> int:
        """Return the total number of misconceptions in the catalog."""
        return len(self.catalog_data.misconceptions)
