"""Zaruba statistics repository."""

from typing import Optional

from src.bot.models.zaruba import ZarubaStats
from src.bot.models.user import ChatUser
from src.bot.repositories.base import BaseRepository


class ZarubaStatsRepository(BaseRepository):
    """Repository for zaruba statistics operations."""

    def _migrate_legacy_stats(self, chat_id: int, user: ChatUser) -> None:
        """Copy matching legacy stats into the stable-ID table when possible."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT zarub_initiated, zarub_reg, zarub_canceled, zarub_unreg "
                "FROM zarubbl WHERE chat_id = ? AND person_name = ?",
                (chat_id, user.display_name),
            )
            row = cursor.fetchone()
            if row is None:
                return

            cursor.execute(
                "INSERT OR IGNORE INTO zarubbl_by_id "
                "(user_id, chat_id, display_name, zarub_initiated, zarub_reg, zarub_canceled, zarub_unreg) "
                "VALUES (?, ?, ?, 0, 0, 0, 0)",
                (user.user_id, chat_id, user.display_name),
            )
            cursor.execute(
                "UPDATE zarubbl_by_id SET "
                "display_name = ?, "
                "zarub_initiated = zarub_initiated + ?, "
                "zarub_reg = zarub_reg + ?, "
                "zarub_canceled = zarub_canceled + ?, "
                "zarub_unreg = zarub_unreg + ? "
                "WHERE user_id = ? AND chat_id = ?",
                (user.display_name, row[0], row[1], row[2], row[3], user.user_id, chat_id),
            )
            cursor.execute(
                "DELETE FROM zarubbl WHERE chat_id = ? AND person_name = ?",
                (chat_id, user.display_name),
            )

    def get_stats(
        self,
        chat_id: int,
        person_name: str,
        user_id: int | None = None,
    ) -> Optional[ZarubaStats]:
        """Get zaruba stats for a user in a chat."""
        if user_id is not None:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT display_name, chat_id, user_id, zarub_initiated, zarub_reg, "
                    "zarub_canceled, zarub_unreg FROM zarubbl_by_id "
                    "WHERE chat_id = ? AND user_id = ?",
                    (chat_id, user_id),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return ZarubaStats(
                    person_name=row[0],
                    chat_id=row[1],
                    user_id=row[2],
                    zarub_initiated=row[3],
                    zarub_reg=row[4],
                    zarub_canceled=row[5],
                    zarub_unreg=row[6],
                )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT person_name, chat_id, zarub_initiated, zarub_reg, "
                "zarub_canceled, zarub_unreg FROM zarubbl "
                "WHERE chat_id = ? AND person_name = ?",
                (chat_id, person_name),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return ZarubaStats(
                person_name=row[0],
                chat_id=row[1],
                zarub_initiated=row[2],
                zarub_reg=row[3],
                zarub_canceled=row[4],
                zarub_unreg=row[5],
            )

    def increment_counter(
        self,
        chat_id: int,
        person_name: str,
        counter_type: str,
        user_id: int | None = None,
    ) -> None:
        """Increment a zaruba counter for a user.

        Args:
            chat_id: The chat ID
            person_name: The username
            counter_type: One of 'initiate', 'reg', 'cancel', 'unreg'
        """
        column_map = {
            "initiate": "zarub_initiated",
            "reg": "zarub_reg",
            "cancel": "zarub_canceled",
            "unreg": "zarub_unreg",
        }
        column = column_map.get(counter_type, "zarub_unreg")

        if user_id is not None:
            user = ChatUser(user_id=user_id, display_name=person_name)
            self._migrate_legacy_stats(chat_id, user)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO zarubbl_by_id (user_id, chat_id, display_name) "
                    "VALUES (?, ?, ?)",
                    (user_id, chat_id, person_name),
                )
                cursor.execute(
                    f"UPDATE zarubbl_by_id SET {column} = {column} + 1, display_name = ? "
                    "WHERE user_id = ? AND chat_id = ?",
                    (person_name, user_id, chat_id),
                )
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Insert if not exists
            cursor.execute(
                "INSERT OR IGNORE INTO zarubbl (person_name, chat_id) VALUES (?, ?)",
                (person_name, chat_id),
            )
            # Update counter
            cursor.execute(
                f"UPDATE zarubbl SET {column} = {column} + 1 "
                "WHERE person_name = ? AND chat_id = ?",
                (person_name, chat_id),
            )


# Module-level functions for backwards compatibility
_default_repo: Optional[ZarubaStatsRepository] = None


def _get_repo(db_path: Optional[str] = None) -> ZarubaStatsRepository:
    global _default_repo
    if db_path:
        return ZarubaStatsRepository(db_path)
    if _default_repo is None:
        _default_repo = ZarubaStatsRepository()
    return _default_repo


def change_zarubbl_counter(
    person_name: str,
    chat_id: int,
    type: str,
    db_path: Optional[str] = None,
) -> None:
    """Increment a zaruba counter for a user."""
    _get_repo(db_path).increment_counter(chat_id, person_name, type)


def get_zarubbl_stats(
    chat_id: int,
    person_name: str,
    db_path: Optional[str] = None,
) -> dict:
    """Get zaruba stats as a dictionary."""
    stats = _get_repo(db_path).get_stats(chat_id, person_name)
    if stats is None:
        raise IndexError(f"No stats for {person_name}")
    return {
        "zarub_initiated": stats.zarub_initiated,
        "zarub_reg": stats.zarub_reg,
        "zarub_canceled": stats.zarub_canceled,
        "zarub_unreg": stats.zarub_unreg,
    }
