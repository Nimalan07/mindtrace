import json
from pathlib import Path
import pytest

from backend.app.diagnosis.concept_graph import (
    ConceptGraph,
    InvalidConceptReferenceError,
)
from backend.app.diagnosis.misconception_library import (
    MisconceptionLibrary,
    MisconceptionNotFoundError,
)
from backend.app.diagnosis.misconception_schemas import (
    DiagnosticQuestion,
    MisconceptionCatalogData,
    MisconceptionRecord,
)

CONCEPT_PATH = Path("data/concepts/physics_force_motion.json")
MISCONCEPTION_PATH = Path("data/misconceptions/physics_force_motion.json")


@pytest.fixture
def concept_graph():
    return ConceptGraph.load_from_json(CONCEPT_PATH)


@pytest.fixture
def misconception_library(concept_graph):
    return MisconceptionLibrary.load_from_json(
        MISCONCEPTION_PATH,
        concept_graph=concept_graph,
    )


# 1. Successful JSON loading
def test_load_catalog_success(misconception_library):
    assert misconception_library.catalog_data.subject == "Physics"
    assert misconception_library.catalog_data.domain == "Classical Mechanics"
    assert len(misconception_library) == 24


# 2. Total record count verification
def test_catalog_record_count(misconception_library):
    records = misconception_library.get_all_misconceptions()
    assert len(records) == 24
    assert len(misconception_library) == 24


# 3. Lookup by ID success
def test_lookup_by_id_success(misconception_library):
    rec = misconception_library.get_by_id("PHY_M009")
    assert rec.id == "PHY_M009"
    assert "Mass-Dependent" in rec.title
    assert "newton_third_law" in rec.associated_concepts
    assert rec.severity == "high"
    assert len(rec.diagnostic_questions) >= 1


# 4. Lookup by ID raises MisconceptionNotFoundError
def test_lookup_by_id_not_found(misconception_library):
    with pytest.raises(MisconceptionNotFoundError):
        misconception_library.get_by_id("PHY_NONEXISTENT")


# 5. Lookup by concept ID
def test_lookup_by_concept(misconception_library):
    recs = misconception_library.get_by_concept("newton_third_law")
    ids = [r.id for r in recs]
    assert "PHY_M009" in ids
    assert "PHY_M010" in ids


# 6. Lookup by concept with zero associations returns empty list
def test_lookup_by_concept_empty(misconception_library):
    recs = misconception_library.get_by_concept("nonexistent_concept_id")
    assert recs == []


# 7. Search is case-insensitive
def test_search_case_insensitive(misconception_library):
    upper_matches = misconception_library.search("TRUCK")
    lower_matches = misconception_library.search("truck")
    assert len(upper_matches) > 0
    assert len(upper_matches) == len(lower_matches)
    assert any(m.id == "PHY_M009" for m in upper_matches)


# 8. Search across multiple fields (symptoms, reasoning, causes)
def test_search_across_fields(misconception_library):
    # 'impetus' appears in possible_causes of PHY_M003
    matches = misconception_library.search("impetus")
    assert any(m.id == "PHY_M003" for m in matches)

    # 'apex' appears in symptoms/reasoning of PHY_M001
    matches_apex = misconception_library.search("apex")
    assert any(m.id == "PHY_M001" for m in matches_apex)


# 9. Search empty string or whitespace returns empty list
def test_search_empty_query_or_no_match(misconception_library):
    assert misconception_library.search("") == []
    assert misconception_library.search("   ") == []
    assert misconception_library.search("xyznonexistentterm123") == []


# 10. Multi-concept candidate retrieval and ranking
def test_candidates_for_multiple_concepts(misconception_library):
    # PHY_M009 has both 'mass' and 'newton_third_law'
    candidates = misconception_library.get_candidates_for_concepts(
        ["mass", "newton_third_law"]
    )
    assert len(candidates) > 0
    # Top candidate should be PHY_M009 because it matches both concepts
    assert candidates[0].id == "PHY_M009"
    # Ensure no duplicate records in the candidate list
    candidate_ids = [c.id for c in candidates]
    assert len(candidate_ids) == len(set(candidate_ids))


# 11. Multi-concept candidate retrieval with no matches returns empty list
def test_candidates_for_empty_or_unknown_concepts(misconception_library):
    candidates = misconception_library.get_candidates_for_concepts(["unknown_concept_xyz"])
    assert candidates == []
    assert misconception_library.get_candidates_for_concepts([]) == []


# 12. Validate all associated concepts exist in concept graph
def test_validate_against_concept_graph_success(misconception_library, concept_graph):
    assert misconception_library.validate_against_graph(concept_graph) is True


# 13. Invalid concept reference raises InvalidConceptReferenceError
def test_validate_against_concept_graph_failure(concept_graph):
    with MISCONCEPTION_PATH.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Corrupt one concept reference
    raw_data["misconceptions"][0]["associated_concepts"].append("quantum_tunneling")
    catalog_data = MisconceptionCatalogData.model_validate(raw_data)

    with pytest.raises(InvalidConceptReferenceError) as exc_info:
        MisconceptionLibrary(catalog_data, concept_graph=concept_graph)
    assert "quantum_tunneling" in str(exc_info.value)


# 14. Duplicate misconception ID detection
def test_reject_duplicate_misconception_id():
    with MISCONCEPTION_PATH.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Duplicate the first misconception
    duplicate_item = dict(raw_data["misconceptions"][0])
    raw_data["misconceptions"].append(duplicate_item)

    with pytest.raises(ValueError) as exc_info:
        MisconceptionCatalogData.model_validate(raw_data)
    assert "Duplicate misconception IDs" in str(exc_info.value)


# 15. Duplicate question IDs or duplicate concepts in a record rejected
def test_reject_duplicate_question_id_or_concept():
    # Test duplicate concepts within a single record
    with pytest.raises(ValueError) as exc_concept:
        MisconceptionRecord(
            id="TEST_M01",
            title="Test Title",
            associated_concepts=["velocity", "velocity"],
            incorrect_belief="Something wrong",
            correct_understanding="Something right",
            typical_reasoning=["Reasoning"],
            common_symptoms=["Symptom"],
            possible_causes=["Cause"],
            diagnostic_questions=[
                DiagnosticQuestion(
                    question_id="DQ_TEST_1",
                    question="Q?",
                    supporting_evidence="Supp",
                    weakening_evidence="Weak",
                )
            ],
            severity="high",
        )
    assert "Duplicate concept references" in str(exc_concept.value)

    # Test duplicate question IDs across catalog
    with MISCONCEPTION_PATH.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Re-use question_id from M001 in M002
    raw_data["misconceptions"][1]["diagnostic_questions"][0]["question_id"] = (
        raw_data["misconceptions"][0]["diagnostic_questions"][0]["question_id"]
    )
    with pytest.raises(ValueError) as exc_qid:
        MisconceptionCatalogData.model_validate(raw_data)
    assert "Duplicate diagnostic question ID" in str(exc_qid.value)
