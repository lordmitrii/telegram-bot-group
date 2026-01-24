"""Zaruba business logic service."""

from typing import Dict, Optional, Tuple

from src.bot.core.constants import BAD_THRESHOLD
from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.models.zaruba import ZarubaSession, ZarubaStats
from src.bot.repositories.session import SessionRepository, get_session_repo
from src.bot.repositories.zaruba import ZarubaStatsRepository


class ZarubaService:
    """Service for managing zaruba events."""

    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        stats_repo: Optional[ZarubaStatsRepository] = None,
    ):
        self._session_repo = session_repo or get_session_repo()
        self._stats_repo = stats_repo or ZarubaStatsRepository()

    def create_zaruba(
        self,
        chat_id: int,
        time: str,
        creator_username: str,
    ) -> ZarubaSession:
        """Create a new zaruba session.

        Args:
            chat_id: The chat ID
            time: The zaruba time
            creator_username: The username of the creator

        Returns:
            The created ZarubaSession
        """
        session = self._session_repo.create_session(
            chat_id=chat_id,
            zaruba_time=time,
            initial_user=creator_username,
        )
        self._stats_repo.increment_counter(chat_id, creator_username, "initiate")
        return session

    def register_user(
        self,
        chat_id: int,
        username: str,
        time: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Register a user for the zaruba.

        Args:
            chat_id: The chat ID
            username: The username to register
            time: Optional custom time (uses zaruba time if not provided)

        Returns:
            Tuple of (success, actual_time)

        Raises:
            NoActiveZarubaError: If no active zaruba exists
        """
        session = self._session_repo.get_session(chat_id)
        if session is None:
            raise NoActiveZarubaError()

        reg_time = time or session.zaruba_time
        self._session_repo.register_user(chat_id, username, reg_time)
        self._stats_repo.increment_counter(chat_id, username, "reg")
        return True, reg_time

    def unregister_user(self, chat_id: int, username: str) -> bool:
        """Unregister a user from the zaruba.

        Args:
            chat_id: The chat ID
            username: The username to unregister

        Returns:
            True if user was unregistered, False if not found
        """
        if self._session_repo.unregister_user(chat_id, username):
            self._stats_repo.increment_counter(chat_id, username, "unreg")
            return True
        return False

    def cancel_zaruba(self, chat_id: int, username: str) -> bool:
        """Cancel the active zaruba session.

        Args:
            chat_id: The chat ID
            username: The username of the person canceling

        Returns:
            True if canceled, False if no active session

        Raises:
            NoActiveZarubaError: If no active zaruba exists
        """
        if not self._session_repo.has_active_session(chat_id):
            raise NoActiveZarubaError()

        self._session_repo.delete_session(chat_id)
        self._stats_repo.increment_counter(chat_id, username, "cancel")
        return True

    def get_session(self, chat_id: int) -> Optional[ZarubaSession]:
        """Get the active zaruba session for a chat."""
        return self._session_repo.get_session(chat_id)

    def get_registered_users(self, chat_id: int) -> Dict[str, str]:
        """Get the registered users for a chat's zaruba.

        Returns:
            Dict mapping username to registration time
        """
        session = self._session_repo.get_session(chat_id)
        if session is None:
            return {}
        return session.registered_users

    def get_user_stats(self, chat_id: int, username: str) -> ZarubaStats:
        """Get user statistics.

        Raises:
            StatsNotFoundError: If no stats found for user
        """
        stats = self._stats_repo.get_stats(chat_id, username)
        if stats is None:
            raise StatsNotFoundError(username)
        return stats

    def evaluate_user_reliability(
        self,
        stats: ZarubaStats,
    ) -> Tuple[bool, float]:
        """Evaluate if a user is reliable based on their stats.

        Args:
            stats: The user's zaruba stats

        Returns:
            Tuple of (is_reliable, chance_percentage)
        """
        chance = stats.reliability_score
        is_reliable = chance < BAD_THRESHOLD
        return is_reliable, round(chance * 100, 2)
