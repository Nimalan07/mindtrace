import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import networkx as nx

from backend.app.diagnosis.schemas import ConceptNode, PrerequisiteGraphData


class ConceptGraphError(Exception):
    """Base exception for concept graph operations."""

    pass


class CircularDependencyError(ConceptGraphError):
    """Raised when a circular prerequisite cycle is detected."""

    pass


class InvalidConceptReferenceError(ConceptGraphError):
    """Raised when an unknown concept ID is referenced."""

    pass


class ConceptGraph:
    """Generic, subject-independent prerequisite concept graph engine."""

    def __init__(self, graph_data: PrerequisiteGraphData) -> None:
        self.graph_data = graph_data
        self.graph = nx.DiGraph()
        self._build_graph()
        self.validate_graph()

    def _build_graph(self) -> None:
        """Populate nodes and directed edges from the graph data."""
        for concept in self.graph_data.concepts:
            self.graph.add_node(
                concept.id,
                name=concept.name,
                topic=concept.topic,
                description=concept.description,
                related_concepts=concept.related_concepts,
            )

        for concept in self.graph_data.concepts:
            for prerequisite in concept.prerequisites:
                self.graph.add_edge(
                    prerequisite,
                    concept.id,
                )

    @classmethod
    def load_from_json(cls, file_path: Union[str, Path]) -> "ConceptGraph":
        """Load, validate, and instantiate a ConceptGraph from a JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Concept graph file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        graph_data = PrerequisiteGraphData.model_validate(raw_data)
        return cls(graph_data)

    def validate_graph(self) -> bool:
        """Check that the graph is a valid directed acyclic graph."""
        if not nx.is_directed_acyclic_graph(self.graph):
            cycle = nx.find_cycle(self.graph)
            cycle_path = " -> ".join(
                [edge[0] for edge in cycle] + [cycle[-1][1]]
            )
            raise CircularDependencyError(
                f"Circular prerequisite dependency detected: {cycle_path}"
            )
        return True

    def _check_concept(self, concept_id: str) -> None:
        """Ensure the requested concept exists."""
        if concept_id not in self.graph:
            raise InvalidConceptReferenceError(
                f"Unknown concept ID: '{concept_id}'"
            )

    def get_concept(self, concept_id: str) -> Dict[str, Any]:
        """Return metadata for a concept."""
        self._check_concept(concept_id)
        node_data = dict(self.graph.nodes[concept_id])
        node_data["id"] = concept_id
        return node_data

    def get_all_concepts(self) -> List[str]:
        """Return all registered concept IDs."""
        return list(self.graph.nodes)

    def get_direct_prerequisites(self, concept_id: str) -> List[str]:
        """Return immediate prerequisites of a concept."""
        self._check_concept(concept_id)
        return sorted(self.graph.predecessors(concept_id))

    def get_all_prerequisites(self, concept_id: str) -> List[str]:
        """
        Return every prerequisite in the dependency chain.
        Results are returned in learning order.
        """
        self._check_concept(concept_id)
        ancestors = nx.ancestors(self.graph, concept_id)
        prerequisite_graph = self.graph.subgraph(ancestors)
        return list(
            nx.lexicographical_topological_sort(prerequisite_graph)
        )

    def get_missing_prerequisites(
        self, concept_id: str, mastered_concepts: List[str]
    ) -> List[str]:
        """
        Identify which prerequisites in the dependency chain are not yet mastered.
        Validates that concept_id and all mastered_concepts exist in the graph.
        """
        self._check_concept(concept_id)
        for mastered in mastered_concepts:
            self._check_concept(mastered)

        mastered_set = set(mastered_concepts)
        all_prereqs = self.get_all_prerequisites(concept_id)
        return [
            prereq for prereq in all_prereqs if prereq not in mastered_set
        ]

    def get_learning_order(
        self, target_concepts: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate a topologically sorted learning order for target concepts
        (including their prerequisites) or for the complete graph.
        """
        if target_concepts is None:
            return list(nx.lexicographical_topological_sort(self.graph))

        for target in target_concepts:
            self._check_concept(target)

        needed_nodes = set(target_concepts)
        for target in target_concepts:
            needed_nodes.update(nx.ancestors(self.graph, target))

        subgraph = self.graph.subgraph(needed_nodes)
        return list(nx.lexicographical_topological_sort(subgraph))

    def get_related_concepts(self, concept_id: str) -> List[str]:
        """Return associated concepts that are not prerequisite DAG edges."""
        self._check_concept(concept_id)
        return self.graph.nodes[concept_id].get("related_concepts", [])

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Return summary statistics of the concept graph."""
        return {
            "concept_nodes": self.graph.number_of_nodes(),
            "prerequisite_edges": self.graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
        }
