from datetime import datetime, timedelta, timezone
import pytest

from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionEngine


@pytest.fixture
def sr_engine() -> SpacedRepetitionEngine:
    return SpacedRepetitionEngine()


def test_schedule_initial_card(sr_engine: SpacedRepetitionEngine):
    card = sr_engine.schedule_initial_card("student_1", "net_force")
    assert card.student_id == "student_1"
    assert card.concept_id == "net_force"
    assert card.ease_factor == 2.5
    assert card.interval_days == 1.0
    assert card.repetition_count == 0


def test_sm2_successful_review_streak(sr_engine: SpacedRepetitionEngine):
    now = datetime.now(timezone.utc)
    # First successful review (q=5)
    c1 = sr_engine.record_review("student_1", "net_force", quality_score=5, as_of_date=now)
    assert c1.repetition_count == 1
    assert c1.interval_days == 1.0
    assert c1.ease_factor >= 2.5

    # Second successful review (q=5)
    c2 = sr_engine.record_review("student_1", "net_force", quality_score=5, as_of_date=now)
    assert c2.repetition_count == 2
    assert c2.interval_days == 6.0

    # Third successful review (q=5)
    c3 = sr_engine.record_review("student_1", "net_force", quality_score=5, as_of_date=now)
    assert c3.repetition_count == 3
    assert c3.interval_days > 6.0


def test_sm2_failed_review_resets(sr_engine: SpacedRepetitionEngine):
    now = datetime.now(timezone.utc)
    # Build up to 2 repetitions
    sr_engine.record_review("student_1", "net_force", quality_score=4, as_of_date=now)
    sr_engine.record_review("student_1", "net_force", quality_score=4, as_of_date=now)

    # Fail review (q=1)
    c_fail = sr_engine.record_review("student_1", "net_force", quality_score=1, as_of_date=now)
    assert c_fail.repetition_count == 0
    assert c_fail.interval_days == 1.0


def test_due_cards_detection(sr_engine: SpacedRepetitionEngine):
    now = datetime.now(timezone.utc)
    sr_engine.schedule_initial_card("student_1", "concept_due", initial_interval_days=1.0)
    # Check tomorrow
    tomorrow = now + timedelta(days=2)
    due = sr_engine.get_due_cards("student_1", as_of_date=tomorrow)
    assert len(due) == 1
    assert due[0].concept_id == "concept_due"
    assert due[0].urgency_score > 0
