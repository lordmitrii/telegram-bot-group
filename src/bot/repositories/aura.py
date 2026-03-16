"""Aura repository."""

from typing import Optional

from src.bot.models.aura import UserAura
from src.bot.models.user import ChatUser
from src.bot.repositories.base import BaseRepository


class AuraRepository(BaseRepository):
    """Repository for user aura operations."""

    def _migrate_legacy_aura(self, chat_id: int, user: ChatUser) -> None:
        """Copy matching legacy aura into the stable-ID table when possible."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT aura_points FROM user_aura WHERE chat_id = ? AND person_name = ?",
                (chat_id, user.display_name),
            )
            row = cursor.fetchone()
            if row is None:
                return

            cursor.execute(
                "INSERT OR IGNORE INTO user_aura_by_id (user_id, chat_id, display_name, aura_points) "
                "VALUES (?, ?, ?, 0)",
                (user.user_id, chat_id, user.display_name),
            )
            cursor.execute(
                "UPDATE user_aura_by_id "
                "SET aura_points = aura_points + ?, display_name = ? "
                "WHERE user_id = ? AND chat_id = ?",
                (row[0], user.display_name, user.user_id, chat_id),
            )
            cursor.execute(
                "DELETE FROM user_aura WHERE chat_id = ? AND person_name = ?",
                (chat_id, user.display_name),
            )

    def get_aura(
        self,
        chat_id: int,
        person_name: str,
        user_id: int | None = None,
    ) -> UserAura:
        """Get aura for a user, defaulting to zero when absent."""
        if user_id is not None:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT display_name, chat_id, aura_points, user_id FROM user_aura_by_id "
                    "WHERE chat_id = ? AND user_id = ?",
                    (chat_id, user_id),
                )
                row = cursor.fetchone()
                if row is None:
                    return UserAura(
                        person_name=person_name,
                        chat_id=chat_id,
                        aura_points=0,
                        user_id=user_id,
                    )
                return UserAura(
                    person_name=row[0],
                    chat_id=row[1],
                    aura_points=row[2],
                    user_id=row[3],
                )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT person_name, chat_id, aura_points FROM user_aura "
                "WHERE chat_id = ? AND person_name = ?",
                (chat_id, person_name),
            )
            row = cursor.fetchone()
            if row is None:
                return UserAura(person_name=person_name, chat_id=chat_id, aura_points=0)
            return UserAura(person_name=row[0], chat_id=row[1], aura_points=row[2])

    def change_points(
        self,
        chat_id: int,
        person_name: str,
        points: int,
        user_id: int | None = None,
    ) -> UserAura:
        """Add or subtract aura points for a user."""
        if user_id is not None:
            user = ChatUser(user_id=user_id, display_name=person_name)
            self._migrate_legacy_aura(chat_id, user)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO user_aura_by_id (user_id, chat_id, display_name) "
                    "VALUES (?, ?, ?)",
                    (user_id, chat_id, person_name),
                )
                cursor.execute(
                    "UPDATE user_aura_by_id "
                    "SET aura_points = aura_points + ?, display_name = ? "
                    "WHERE user_id = ? AND chat_id = ?",
                    (points, person_name, user_id, chat_id),
                )
            return self.get_aura(chat_id, person_name, user_id=user_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO user_aura (person_name, chat_id) VALUES (?, ?)",
                (person_name, chat_id),
            )
            cursor.execute(
                "UPDATE user_aura SET aura_points = aura_points + ? "
                "WHERE person_name = ? AND chat_id = ?",
                (points, person_name, chat_id),
            )

        return self.get_aura(chat_id, person_name)


_default_repo: Optional[AuraRepository] = None


def get_aura_repo(db_path: Optional[str] = None) -> AuraRepository:
    """Get the default aura repository."""
    global _default_repo
    if db_path:
        return AuraRepository(db_path)
    if _default_repo is None:
        _default_repo = AuraRepository()
    return _default_repo
