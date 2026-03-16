"""Repository for chat-scoped Telegram user identities."""

from typing import Optional

from src.bot.models.user import ChatUser
from src.bot.repositories.base import BaseRepository


class UserIdentityRepository(BaseRepository):
    """Stores the latest known identity for Telegram users within a chat."""

    def upsert_user(self, chat_id: int, user: ChatUser) -> None:
        """Insert or update the latest display info for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_identities (chat_id, user_id, username, display_name) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(chat_id, user_id) DO UPDATE SET "
                "username = excluded.username, "
                "display_name = excluded.display_name",
                (chat_id, user.user_id, user.username, user.display_name),
            )

    def get_by_user_id(self, chat_id: int, user_id: int) -> Optional[ChatUser]:
        """Get a known user by Telegram user ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, display_name, username "
                "FROM user_identities WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return ChatUser(user_id=row[0], display_name=row[1], username=row[2])

    def get_by_username(self, chat_id: int, username: str) -> Optional[ChatUser]:
        """Resolve a username to the latest known Telegram user identity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, display_name, username "
                "FROM user_identities WHERE chat_id = ? AND username = ?",
                (chat_id, username),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return ChatUser(user_id=row[0], display_name=row[1], username=row[2])


_default_repo: Optional[UserIdentityRepository] = None


def get_user_identity_repo(db_path: Optional[str] = None) -> UserIdentityRepository:
    """Get the default identity repository."""
    global _default_repo
    if db_path:
        return UserIdentityRepository(db_path)
    if _default_repo is None:
        _default_repo = UserIdentityRepository()
    return _default_repo
