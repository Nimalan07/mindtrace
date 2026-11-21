from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from backend.app.adaptive_learning.assessment_schemas import AssessmentEvaluation
from backend.app.adaptive_learning.intervention_schemas import InterventionPlan
from backend.app.adaptive_learning.learner_model import ConceptMasteryRecord, LearnerProfile
from backend.app.adaptive_learning.spaced_repetition import SpacedRepetitionCard


class AdaptiveRepository:
    """Interface for persisting adaptive learning and assessment state."""

    def save_profile(self, profile: LearnerProfile) -> None:
        raise NotImplementedError

    def get_profile(self, student_id: str) -> Optional[LearnerProfile]:
        raise NotImplementedError

    def list_all_profiles(self) -> List[LearnerProfile]:
        raise NotImplementedError

    def save_spaced_card(self, card: SpacedRepetitionCard) -> None:
        raise NotImplementedError

    def get_spaced_cards(self, student_id: str) -> List[SpacedRepetitionCard]:
        raise NotImplementedError

    def save_intervention(self, plan: InterventionPlan) -> None:
        raise NotImplementedError

    def get_intervention(self, session_id: str) -> Optional[InterventionPlan]:
        raise NotImplementedError


class SQLiteAdaptiveRepository(AdaptiveRepository):
    """
    SQLite-backed persistence for learner models, assessments, revision schedules,
    and personalized interventions.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._shared_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS learner_profiles (
                student_id TEXT PRIMARY KEY,
                overall_proficiency REAL NOT NULL,
                total_assessments INTEGER NOT NULL,
                total_correct INTEGER NOT NULL,
                profile_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS spaced_repetition_cards (
                student_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                ease_factor REAL NOT NULL,
                interval_days REAL NOT NULL,
                repetition_count INTEGER NOT NULL,
                next_review_due TIMESTAMP NOT NULL,
                last_reviewed_at TIMESTAMP NOT NULL,
                card_json TEXT NOT NULL,
                PRIMARY KEY (student_id, concept_id)
            );

            CREATE TABLE IF NOT EXISTS intervention_plans (
                session_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                target_concept_id TEXT NOT NULL,
                intervention_type TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()

    def save_profile(self, profile: LearnerProfile) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO learner_profiles (
                student_id, overall_proficiency, total_assessments, total_correct, profile_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                profile.student_id,
                profile.overall_proficiency,
                profile.total_assessments,
                profile.total_correct,
                profile.model_dump_json(),
            ),
        )
        conn.commit()

    def get_profile(self, student_id: str) -> Optional[LearnerProfile]:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT profile_json FROM learner_profiles WHERE student_id = ?",
            (student_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return LearnerProfile.model_validate_json(row["profile_json"])

    def list_all_profiles(self) -> List[LearnerProfile]:
        conn = self._get_connection()
        cursor = conn.execute("SELECT profile_json FROM learner_profiles")
        return [LearnerProfile.model_validate_json(row["profile_json"]) for row in cursor.fetchall()]

    def save_spaced_card(self, card: SpacedRepetitionCard) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO spaced_repetition_cards (
                student_id, concept_id, ease_factor, interval_days, repetition_count,
                next_review_due, last_reviewed_at, card_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card.student_id,
                card.concept_id,
                card.ease_factor,
                card.interval_days,
                card.repetition_count,
                card.next_review_due.isoformat(),
                card.last_reviewed_at.isoformat(),
                card.model_dump_json(),
            ),
        )
        conn.commit()

    def get_spaced_cards(self, student_id: str) -> List[SpacedRepetitionCard]:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT card_json FROM spaced_repetition_cards WHERE student_id = ?",
            (student_id,),
        )
        return [SpacedRepetitionCard.model_validate_json(row["card_json"]) for row in cursor.fetchall()]

    def save_intervention(self, plan: InterventionPlan) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO intervention_plans (
                session_id, student_id, target_concept_id, intervention_type, plan_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                plan.session_id,
                plan.student_id,
                plan.target_concept_id,
                plan.intervention_type.value,
                plan.model_dump_json(),
            ),
        )
        conn.commit()

    def get_intervention(self, session_id: str) -> Optional[InterventionPlan]:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT plan_json FROM intervention_plans WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return InterventionPlan.model_validate_json(row["plan_json"])
