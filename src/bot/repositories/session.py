"""Session repository for per-chat zaruba state management."""

import json
from typing import Dict, Optional

from src.bot.models.zaruba import ZarubaSession
from src.bot.repositories.base import BaseRepository


class SessionRepository(BaseRepository):
    """Repository for managing per-chat zaruba sessions.

    This replaces the global state variables (zaruba_time, registered_users)
    with database-backed per-chat state.
    """

    def get_session(self, chat_id: int) -> Optional[ZarubaSession]:
        """Get the zaruba session for a chat."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chat_id, zaruba_time, registered_users, botinok_votes, "
                "fined_users, absence_penalties, created_at "
                "FROM zaruba_sessions WHERE chat_id = ?",
                (chat_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            registered_users = json.loads(row[2]) if row[2] else {}
            botinok_votes = json.loads(row[3]) if row[3] else {}
            fined_users = json.loads(row[4]) if row[4] else []
            absence_penalties = json.loads(row[5]) if row[5] else []
            return ZarubaSession(
                chat_id=row[0],
                zaruba_time=row[1],
                registered_users=registered_users,
                botinok_votes=botinok_votes,
                fined_users=fined_users,
                absence_penalties=absence_penalties,
                created_at=row[6],
            )

    def get_all_sessions(self) -> list[ZarubaSession]:
        """Get all active zaruba sessions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chat_id, zaruba_time, registered_users, botinok_votes, "
                "fined_users, absence_penalties, created_at "
                "FROM zaruba_sessions"
            )
            rows = cursor.fetchall()

        sessions: list[ZarubaSession] = []
        for row in rows:
            sessions.append(
                ZarubaSession(
                    chat_id=row[0],
                    zaruba_time=row[1],
                    registered_users=json.loads(row[2]) if row[2] else {},
                    botinok_votes=json.loads(row[3]) if row[3] else {},
                    fined_users=json.loads(row[4]) if row[4] else [],
                    absence_penalties=json.loads(row[5]) if row[5] else [],
                    created_at=row[6],
                )
            )
        return sessions

    def create_session(
        self,
        chat_id: int,
        zaruba_time: str,
        initial_user: Optional[str] = None,
    ) -> ZarubaSession:
        """Create a new zaruba session for a chat."""
        registered_users: Dict[str, str] = {}
        if initial_user:
            registered_users[initial_user] = zaruba_time

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO zaruba_sessions "
                "(chat_id, zaruba_time, registered_users, botinok_votes, fined_users, absence_penalties) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    chat_id,
                    zaruba_time,
                    json.dumps(registered_users),
                    json.dumps({}),
                    json.dumps([]),
                    json.dumps([]),
                ),
            )

        return ZarubaSession(
            chat_id=chat_id,
            zaruba_time=zaruba_time,
            registered_users=registered_users,
        )

    def save_session(self, session: ZarubaSession) -> None:
        """Persist mutable session state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE zaruba_sessions "
                "SET registered_users = ?, botinok_votes = ?, fined_users = ?, absence_penalties = ? "
                "WHERE chat_id = ?",
                (
                    json.dumps(session.registered_users),
                    json.dumps(session.botinok_votes),
                    json.dumps(session.fined_users),
                    json.dumps(session.absence_penalties),
                    session.chat_id,
                ),
            )

    def register_user(
        self,
        chat_id: int,
        username: str,
        time: str,
    ) -> bool:
        """Register a user for the zaruba session.

        Returns True if successful, False if no session exists.
        """
        session = self.get_session(chat_id)
        if session is None:
            return False
        session.registered_users[username] = time
        self.save_session(session)
        return True

    def unregister_user(self, chat_id: int, username: str) -> bool:
        """Unregister a user from the zaruba session.

        Returns True if user was registered, False otherwise.
        """
        session = self.get_session(chat_id)
        if session is None:
            return False
        if username not in session.registered_users:
            return False
        del session.registered_users[username]
        self.save_session(session)
        return True

    def delete_session(self, chat_id: int) -> bool:
        """Delete the zaruba session for a chat.

        Returns True if a session was deleted, False if none existed.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM zaruba_sessions WHERE chat_id = ?",
                (chat_id,),
            )
            return cursor.rowcount > 0

    def delete_all_sessions(self) -> int:
        """Delete all zaruba sessions.

        Returns the number of deleted sessions.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM zaruba_sessions")
            return cursor.rowcount

    def has_active_session(self, chat_id: int) -> bool:
        """Check if a chat has an active zaruba session."""
        return self.get_session(chat_id) is not None


# Module-level instance for convenience
_default_repo: Optional[SessionRepository] = None


def get_session_repo(db_path: Optional[str] = None) -> SessionRepository:
    """Get the default session repository."""
    global _default_repo
    if db_path:
        return SessionRepository(db_path)
    if _default_repo is None:
        _default_repo = SessionRepository()
    return _default_repo
