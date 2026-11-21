from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SpacedRepetitionCard(BaseModel):
    """Memory retention card representing a student's spaced revision schedule for a concept."""

    model_config = ConfigDict(extra="forbid")

    student_id: str
    concept_id: str
    ease_factor: float = Field(default=2.5, ge=1.3)
    interval_days: float = Field(default=1.0, ge=0.5)
    repetition_count: int = Field(default=0, ge=0)
    last_reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_review_due: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=1))
    total_reviews: int = Field(default=0, ge=0)
    urgency_score: float = Field(default=0.0)


class SpacedRepetitionEngine:
    """
    SuperMemo SM-2 spaced repetition scheduler customized for concept revision
    and retention maintenance.
    """

    def __init__(self, min_ease_factor: float = 1.3) -> None:
        self.min_ease_factor = min_ease_factor
        self._cards: Dict[str, Dict[str, SpacedRepetitionCard]] = {}  # student_id -> {concept_id -> Card}

    def schedule_initial_card(
        self,
        student_id: str,
        concept_id: str,
        initial_interval_days: float = 1.0,
    ) -> SpacedRepetitionCard:
        """Initialize or retrieve a spaced repetition card for a newly introduced concept."""
        student_cards = self._cards.setdefault(student_id, {})
        if concept_id in student_cards:
            return student_cards[concept_id]

        now = datetime.now(timezone.utc)
        due = now + timedelta(days=initial_interval_days)
        card = SpacedRepetitionCard(
            student_id=student_id,
            concept_id=concept_id,
            ease_factor=2.5,
            interval_days=initial_interval_days,
            repetition_count=0,
            last_reviewed_at=now,
            next_review_due=due,
            total_reviews=0,
            urgency_score=0.0,
        )
        student_cards[concept_id] = card
        return card

    def record_review(
        self,
        student_id: str,
        concept_id: str,
        quality_score: int,  # 0 to 5
        as_of_date: Optional[datetime] = None,
    ) -> SpacedRepetitionCard:
        """
        Apply SM-2 algorithm update given recall quality score (0..5).
        - 5: Perfect recall
        - 4: Correct after minor hesitation
        - 3: Correct with difficulty
        - 2: Incorrect, remembered upon reveal
        - 1: Incorrect, completely forgotten
        - 0: Total blank or reinforced misconception
        """
        q = max(0, min(5, quality_score))
        now = as_of_date or datetime.now(timezone.utc)

        card = self.schedule_initial_card(student_id, concept_id)

        # 1. Update ease factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        delta_ef = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        card.ease_factor = max(self.min_ease_factor, round(card.ease_factor + delta_ef, 4))

        # 2. Update repetition count and interval
        if q < 3:
            # Failed recall: reset repetitions and schedule prompt revision
            card.repetition_count = 0
            card.interval_days = 1.0
        else:
            # Successful recall
            if card.repetition_count == 0:
                card.interval_days = 1.0
            elif card.repetition_count == 1:
                card.interval_days = 6.0
            else:
                card.interval_days = round(card.interval_days * card.ease_factor, 1)

            card.repetition_count += 1

        card.total_reviews += 1
        card.last_reviewed_at = now
        card.next_review_due = now + timedelta(days=card.interval_days)

        return card

    def get_due_cards(
        self,
        student_id: str,
        as_of_date: Optional[datetime] = None,
    ) -> List[SpacedRepetitionCard]:
        """Fetch all cards whose next review date is earlier than or equal to as_of_date."""
        ref_time = as_of_date or datetime.now(timezone.utc)
        student_cards = self._cards.get(student_id, {})
        due: List[SpacedRepetitionCard] = []

        for card in student_cards.values():
            if card.next_review_due <= ref_time:
                # Calculate urgency: overdue days
                overdue_seconds = (ref_time - card.next_review_due).total_seconds()
                card.urgency_score = round(max(0.0, overdue_seconds / 86400.0) + 1.0, 2)
                due.append(card)

        # Sort descending by urgency
        due.sort(key=lambda c: c.urgency_score, reverse=True)
        return due

    def get_priority_revision_queue(
        self,
        student_id: str,
        concept_masteries: Optional[Dict[str, float]] = None,
        limit: int = 10,
        as_of_date: Optional[datetime] = None,
    ) -> List[SpacedRepetitionCard]:
        """
        Rank cards by compound urgency: overdue severity combined with conceptual weakness.
        """
        ref_time = as_of_date or datetime.now(timezone.utc)
        student_cards = self._cards.get(student_id, {})
        masteries = concept_masteries or {}

        all_cards = list(student_cards.values())
        for card in all_cards:
            overdue_days = (ref_time - card.next_review_due).total_seconds() / 86400.0
            p_l = masteries.get(card.concept_id, 0.5)
            # Low mastery amplifies urgency
            weakness_factor = 2.0 - p_l
            card.urgency_score = round(max(0.1, overdue_days + 1.0) * weakness_factor, 2)

        all_cards.sort(key=lambda c: c.urgency_score, reverse=True)
        return all_cards[:limit]
