"""Repository for botinok aura votes."""

from typing import Optional

from src.bot.repositories.base import BaseRepository


class BotinokVoteRepository(BaseRepository):
    """Persist botinok votes independently from zaruba sessions."""

    def has_vote(self, chat_id: int, target_username: str, voter_username: str) -> bool:
        """Check whether a voter has already voted against a target."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM botinok_votes "
                "WHERE chat_id = ? AND target_username = ? AND voter_username = ?",
                (chat_id, target_username, voter_username),
            )
            return cursor.fetchone() is not None

    def add_vote(self, chat_id: int, target_username: str, voter_username: str) -> int:
        """Add a vote and return the current vote count for the target."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO botinok_votes (chat_id, target_username, voter_username) "
                "VALUES (?, ?, ?)",
                (chat_id, target_username, voter_username),
            )
            cursor.execute(
                "SELECT COUNT(*) FROM botinok_votes "
                "WHERE chat_id = ? AND target_username = ?",
                (chat_id, target_username),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def clear_votes(self, chat_id: int, target_username: str) -> None:
        """Clear all votes for a target after the fine is applied."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM botinok_votes WHERE chat_id = ? AND target_username = ?",
                (chat_id, target_username),
            )


_default_repo: Optional[BotinokVoteRepository] = None


def get_botinok_repo(db_path: Optional[str] = None) -> BotinokVoteRepository:
    """Get the default botinok vote repository."""
    global _default_repo
    if db_path:
        return BotinokVoteRepository(db_path)
    if _default_repo is None:
        _default_repo = BotinokVoteRepository()
    return _default_repo
