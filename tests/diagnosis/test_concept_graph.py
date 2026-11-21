import json
from pathlib import Path
import pytest

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    CircularDependencyError,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.schemas import PrerequisiteGraphData

GRAPH_PATH = Path("data/concepts/physics_force_motion.json")


@pytest.fixture
def concept_graph():
    return ConceptGraph.load_from_json(GRAPH_PATH)


def test_graph_statistics(concept_graph):
    stats = concept_graph.get_graph_statistics()
    assert stats["concept_nodes"] == 23
    assert stats["prerequisite_edges"] == 30
    assert stats["is_dag"] is True


def test_direct_prerequisites(concept_graph):
    prereqs = concept_graph.get_direct_prerequisites("newton_second_law")
    assert prereqs == ["acceleration", "mass", "net_force"]


def test_all_prerequisites(concept_graph):
    all_prereqs = concept_graph.get_all_prerequisites("newton_second_law")
    assert "velocity" in all_prereqs
    assert "time_interval" in all_prereqs
    assert "force" in all_prereqs
    assert "net_force" in all_prereqs
    assert "acceleration" in all_prereqs
    assert "mass" in all_prereqs


def test_missing_prerequisites(concept_graph):
    missing = concept_graph.get_missing_prerequisites(
        "kinetic_energy",
        ["mass", "velocity"]
    )
    assert missing == ["speed"]


def test_learning_order(concept_graph):
    learning_order = concept_graph.get_learning_order(
        ["newton_second_law"]
    )
    positions = {
        concept: index
        for index, concept in enumerate(learning_order)
    }
    assert positions["mass"] < positions["newton_second_law"]
    assert positions["force"] < positions["newton_second_law"]
    assert positions["velocity"] < positions["acceleration"]
    assert positions["acceleration"] < positions["newton_second_law"]


def test_related_concepts_are_not_prerequisites(concept_graph):
    related = concept_graph.get_related_concepts(
        "newton_third_law"
    )
    assert "conservation_of_momentum" in related
    assert not concept_graph.graph.has_edge(
        "newton_third_law",
        "conservation_of_momentum"
    )


def test_unknown_concept_raises_error(concept_graph):
    with pytest.raises(InvalidConceptReferenceError):
        concept_graph.get_direct_prerequisites(
            "unknown_concept"
        )


def test_unknown_mastered_concept_raises_error(concept_graph):
    with pytest.raises(InvalidConceptReferenceError):
        concept_graph.get_missing_prerequisites(
            "kinetic_energy",
            ["unknown_concept"]
        )


def test_circular_dependency_is_detected():
    with GRAPH_PATH.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    # Introduce an invalid reverse dependency:
    # acceleration -> velocity
    velocity = next(
        concept
        for concept in raw_data["concepts"]
        if concept["id"] == "velocity"
    )
    velocity["prerequisites"] = ["acceleration"]

    graph_data = PrerequisiteGraphData.model_validate(raw_data)
    with pytest.raises(CircularDependencyError):
        ConceptGraph(graph_data)


def test_learning_order_for_complete_graph(concept_graph):
    order = concept_graph.get_learning_order()
    assert len(order) == 23
