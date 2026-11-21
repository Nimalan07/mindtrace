import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional


class SessionRepository:
    """Abstract interface for persisting and retrieving diagnosis session states."""

    def save_session(self, session_data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        raise NotImplementedError

    def list_sessions(self) -> List[str]:
        raise NotImplementedError


class SQLiteSessionRepository(SessionRepository):
    """
    SQLite-backed repository for diagnosis session state persistence.
    Uses standard library sqlite3 without external dependencies.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        # For :memory:, maintain a persistent connection so tables persist across calls
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_sessions (
                session_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                original_question TEXT NOT NULL,
                original_student_response TEXT NOT NULL,
                extracted_reasoning TEXT NOT NULL,
                first_error_result TEXT NOT NULL,
                diagnostic_session TEXT NOT NULL,
                prerequisite_concepts_to_review TEXT NOT NULL,
                diagnostic_status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()

    def save_session(self, session_data: Dict[str, Any]) -> None:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO diagnosis_sessions (
                session_id, student_id, question_id, original_question,
                original_student_response, extracted_reasoning, first_error_result,
                diagnostic_session, prerequisite_concepts_to_review, diagnostic_status,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                session_data["session_id"],
                session_data["student_id"],
                session_data["question_id"],
                session_data["original_question"],
                session_data["original_student_response"],
                json.dumps(session_data["extracted_reasoning"]),
                json.dumps(session_data["first_error_result"]),
                json.dumps(session_data["diagnostic_session"]),
                json.dumps(session_data.get("prerequisite_concepts_to_review", [])),
                session_data["diagnostic_status"],
            ),
        )
        conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM diagnosis_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "session_id": row["session_id"],
            "student_id": row["student_id"],
            "question_id": row["question_id"],
            "original_question": row["original_question"],
            "original_student_response": row["original_student_response"],
            "extracted_reasoning": json.loads(row["extracted_reasoning"]),
            "first_error_result": json.loads(row["first_error_result"]),
            "diagnostic_session": json.loads(row["diagnostic_session"]),
            "prerequisite_concepts_to_review": json.loads(row["prerequisite_concepts_to_review"]),
            "diagnostic_status": row["diagnostic_status"],
        }

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        existing = self.get_session(session_id)
        if existing is None:
            raise KeyError(f"Session '{session_id}' not found.")

        existing.update(updates)
        self.save_session(existing)

    def list_sessions(self) -> List[str]:
        conn = self._get_connection()
        cursor = conn.execute("SELECT session_id FROM diagnosis_sessions")
        return [row["session_id"] for row in cursor.fetchall()]
