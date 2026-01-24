"""Subscriber repository for managing chat subscriptions."""

from typing import List, Optional

from src.bot.models.subscriber import Subscriber
from src.bot.repositories.base import BaseRepository


class SubscriberRepository(BaseRepository):
    """Repository for subscriber operations."""

    def add(self, chat_id: int) -> None:
        """Add a chat ID to subscribers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)",
                (chat_id,),
            )

    def remove(self, chat_id: int) -> None:
        """Remove a chat ID from subscribers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM subscribers WHERE chat_id = ?",
                (chat_id,),
            )

    def get_all(self) -> List[Subscriber]:
        """Get all subscribers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscribers")
            return [Subscriber(chat_id=row[0]) for row in cursor.fetchall()]

    def get_all_chat_ids(self) -> List[int]:
        """Get all subscriber chat IDs as a list."""
        return [s.chat_id for s in self.get_all()]

    def exists(self, chat_id: int) -> bool:
        """Check if a chat ID is subscribed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM subscribers WHERE chat_id = ?",
                (chat_id,),
            )
            return cursor.fetchone() is not None


# Module-level functions for backwards compatibility
_default_repo: Optional[SubscriberRepository] = None


def _get_repo(db_path: Optional[str] = None) -> SubscriberRepository:
    global _default_repo
    if db_path:
        return SubscriberRepository(db_path)
    if _default_repo is None:
        _default_repo = SubscriberRepository()
    return _default_repo


def add_subscriber(chat_id: int, db_path: Optional[str] = None) -> None:
    """Add a chat ID to subscribers."""
    _get_repo(db_path).add(chat_id)


def remove_subscriber(chat_id: int, db_path: Optional[str] = None) -> None:
    """Remove a chat ID from subscribers."""
    _get_repo(db_path).remove(chat_id)


def get_subscribers(db_path: Optional[str] = None) -> List[int]:
    """Get all subscriber chat IDs."""
    return _get_repo(db_path).get_all_chat_ids()
