from pathlib import Path
import pytest

from backend.app.adaptive_learning.adaptive_question_selector import AdaptiveQuestionSelector
from backend.app.adaptive_learning.assessment_schemas import (
    QuestionDifficulty,
    QuestionModel,
    QuestionType,
)
from backend.app.adaptive_learning.difficulty_engine import AdaptiveDifficultyEngine
from backend.app.adaptive_learning.learner_model import ConceptMasteryRecord, LearnerModel
from backend.app.adaptive_learning.question_bank import QuestionBank
from backend.app.diagnosis.concept_graph import ConceptGraph


@pytest.fixture
def concept_graph() -> ConceptGraph:
    return ConceptGraph.load_from_json("data/concepts/physics_force_motion.json")


@pytest.fixture
def difficulty_engine() -> AdaptiveDifficultyEngine:
    return AdaptiveDifficultyEngine()


def test_difficulty_engine_thresholds(difficulty_engine: AdaptiveDifficultyEngine):
    # Low mastery -> Easy
    diff, _ = difficulty_engine.determine_difficulty(0.20)
    assert diff == QuestionDifficulty.EASY

    # Medium mastery -> Medium
    diff, _ = difficulty_engine.determine_difficulty(0.55)
    assert diff == QuestionDifficulty.MEDIUM

    # High mastery -> Hard
    diff, _ = difficulty_engine.determine_difficulty(0.85)
    assert diff == QuestionDifficulty.HARD


def test_difficulty_streak_promotions(difficulty_engine: AdaptiveDifficultyEngine):
    # 3 correct on Easy promotes to Medium
    diff, _ = difficulty_engine.determine_difficulty(0.30, recent_correct_streak=3)
    assert diff == QuestionDifficulty.MEDIUM

    # 2 incorrect on Medium drops to Easy
    diff, _ = difficulty_engine.determine_difficulty(0.50, recent_incorrect_streak=2)
    assert diff == QuestionDifficulty.EASY


def test_adaptive_question_selector_prerequisite_diversion(concept_graph: ConceptGraph):
    # Setup QuestionBank with real questions
    qb = QuestionBank.load_from_json("data/questions/physics_questions.json", concept_graph=concept_graph)
    learner = LearnerModel()

    selector = AdaptiveQuestionSelector(
        question_bank=qb,
        concept_graph=concept_graph,
        learner_model=learner,
        prerequisite_threshold=0.50,
    )

    # Student wants to practice "acceleration", but direct prerequisite "velocity" has mastery 0.25 (< 0.50)
    res = selector.select_next_question(
        student_id="student_prereq_test",
        target_concept_id="acceleration",
        allow_prerequisite_diversion=True,
    )

    assert res.prerequisite_blocked is True
    # Should have diverted to a prerequisite of acceleration (e.g. velocity)
    assert res.actual_question_concept_id in ["velocity", "time_interval"]
    assert res.question is not None


def test_adaptive_question_selector_no_blocker_when_prereqs_met(concept_graph: ConceptGraph):
    qb = QuestionBank.load_from_json("data/questions/physics_questions.json", concept_graph=concept_graph)
    learner = LearnerModel()

    # Pre-train prerequisites to high mastery
    for p in ["velocity", "time_interval"]:
        learner.get_or_create_profile("student_ready").concept_masteries[p] = ConceptMasteryRecord(
            concept_id=p,
            mastery_probability=0.85,
        )

    selector = AdaptiveQuestionSelector(
        question_bank=qb,
        concept_graph=concept_graph,
        learner_model=learner,
    )

    res = selector.select_next_question(
        student_id="student_ready",
        target_concept_id="acceleration",
    )

    assert res.prerequisite_blocked is False
    assert res.actual_question_concept_id == "acceleration"
