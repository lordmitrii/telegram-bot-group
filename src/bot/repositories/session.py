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
                "SELECT chat_id, zaruba_time, registered_users, created_at "
                "FROM zaruba_sessions WHERE chat_id = ?",
                (chat_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            registered_users = json.loads(row[2]) if row[2] else {}
            return ZarubaSession(
                chat_id=row[0],
                zaruba_time=row[1],
                registered_users=registered_users,
                created_at=row[3],
            )

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
                "(chat_id, zaruba_time, registered_users) VALUES (?, ?, ?)",
                (chat_id, zaruba_time, json.dumps(registered_users)),
            )

        return ZarubaSession(
            chat_id=chat_id,
            zaruba_time=zaruba_time,
            registered_users=registered_users,
        )

    def update_registered_users(
        self,
        chat_id: int,
        registered_users: Dict[str, str],
    ) -> None:
        """Update the registered users for a session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE zaruba_sessions SET registered_users = ? WHERE chat_id = ?",
                (json.dumps(registered_users), chat_id),
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
        self.update_registered_users(chat_id, session.registered_users)
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
        self.update_registered_users(chat_id, session.registered_users)
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
