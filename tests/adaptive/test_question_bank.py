from pathlib import Path
import pytest

from backend.app.adaptive_learning.assessment_schemas import (
    QuestionDifficulty,
    QuestionModel,
    QuestionType,
)
from backend.app.adaptive_learning.question_bank import QuestionBank


@pytest.fixture
def sample_question_bank() -> QuestionBank:
    questions = [
        QuestionModel(
            id="Q_TEST_01",
            title="Test Net Force",
            prompt="A 5 kg box is pulled with 30 N right and 10 N left. What is the net force?",
            concept_id="net_force",
            secondary_concept_ids=["force"],
            difficulty=QuestionDifficulty.EASY,
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A) 40 N", "B) 20 N to the right", "C) 10 N", "D) 300 N"],
            correct_answer="B",
            rubric="Opposing forces subtract: 30 - 10 = 20 N.",
            hints=["Subtract opposing forces."],
            prerequisites=["force"],
            target_misconceptions=["PHY_M008"],
        ),
        QuestionModel(
            id="Q_TEST_02",
            title="Test Numerical Acceleration",
            prompt="Net force of 20 N on 4 kg mass. What is acceleration in m/s²?",
            concept_id="newton_second_law",
            secondary_concept_ids=["net_force", "mass", "acceleration"],
            difficulty=QuestionDifficulty.EASY,
            question_type=QuestionType.NUMERICAL,
            options=[],
            correct_answer="5",
            rubric="a = F / m = 20 / 4 = 5 m/s².",
            hints=["a = F / m"],
            prerequisites=["mass", "net_force", "acceleration"],
            target_misconceptions=[],
        ),
        QuestionModel(
            id="Q_TEST_03",
            title="Test Medium Net Force",
            prompt="Harder net force question",
            concept_id="net_force",
            secondary_concept_ids=[],
            difficulty=QuestionDifficulty.MEDIUM,
            question_type=QuestionType.NUMERICAL,
            options=[],
            correct_answer="15",
            rubric="15 N net force",
            hints=[],
            prerequisites=["force"],
            target_misconceptions=[],
        ),
    ]
    return QuestionBank(questions=questions)


def test_question_bank_indexing(sample_question_bank: QuestionBank):
    assert sample_question_bank.get_question("Q_TEST_01") is not None
    assert sample_question_bank.get_question("NONEXISTENT") is None

    net_force_qs = sample_question_bank.get_questions_by_concept("net_force")
    assert len(net_force_qs) == 3

    # Filter by difficulty
    easy_net_force = sample_question_bank.get_questions_by_concept(
        "net_force", difficulty=QuestionDifficulty.EASY
    )
    assert len(easy_net_force) == 2


def test_question_bank_exclusion(sample_question_bank: QuestionBank):
    qs = sample_question_bank.get_questions_by_concept(
        "net_force", exclude_ids=["Q_TEST_01"]
    )
    assert len(qs) == 2
    assert qs[0].id == "Q_TEST_02"


def test_evaluate_mcq(sample_question_bank: QuestionBank):
    # Direct letter match
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_01", "B")
    assert is_corr is True
    assert score == 1.0

    # Letter with parenthesis
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_01", "B)")
    assert is_corr is True

    # Option text match
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_01", "20 N to the right")
    assert is_corr is True

    # Wrong answer
    is_corr, score, feedback = sample_question_bank.evaluate_answer("Q_TEST_01", "A")
    assert is_corr is False
    assert score == 0.0
    assert "Incorrect" in feedback


def test_evaluate_numerical(sample_question_bank: QuestionBank):
    # Exact match
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_02", "5")
    assert is_corr is True
    assert score == 1.0

    # Float with units
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_02", "5.0 m/s^2")
    assert is_corr is True

    # Slight float precision within 3% tolerance
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_02", "5.05")
    assert is_corr is True

    # Wrong number
    is_corr, score, _ = sample_question_bank.evaluate_answer("Q_TEST_02", "10")
    assert is_corr is False
    assert score == 0.0


def test_load_default_questions_json():
    qb = QuestionBank.load_from_json("data/questions/physics_questions.json")
    all_qs = qb.get_all_questions()
    assert len(all_qs) >= 30

    # Check key concepts are populated
    assert len(qb.get_questions_by_concept("net_force")) >= 2
    assert len(qb.get_questions_by_concept("newton_second_law")) >= 2
    assert len(qb.get_questions_by_concept("velocity")) >= 2
    assert len(qb.get_questions_by_concept("work")) >= 2
