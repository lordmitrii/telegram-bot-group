"""Zaruba business logic service."""

from typing import Dict, Optional, Tuple

from src.bot.core.constants import BAD_THRESHOLD
from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.i18n.messages import MESSAGES
from src.bot.models.aura import UserAura
from src.bot.models.user import ChatUser
from src.bot.models.zaruba import ZarubaSession, ZarubaStats
from src.bot.repositories.aura import AuraRepository, get_aura_repo
from src.bot.repositories.botinok import BotinokVoteRepository, get_botinok_repo
from src.bot.repositories.session import SessionRepository, get_session_repo
from src.bot.repositories.user_identity import (
    UserIdentityRepository,
    get_user_identity_repo,
)
from src.bot.repositories.zaruba import ZarubaStatsRepository


class ZarubaService:
    """Service for managing zaruba events."""

    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        stats_repo: Optional[ZarubaStatsRepository] = None,
        aura_repo: Optional[AuraRepository] = None,
        botinok_repo: Optional[BotinokVoteRepository] = None,
        user_repo: Optional[UserIdentityRepository] = None,
    ):
        self._session_repo = session_repo or get_session_repo()
        self._stats_repo = stats_repo or ZarubaStatsRepository()
        self._aura_repo = aura_repo or get_aura_repo()
        self._botinok_repo = botinok_repo or get_botinok_repo()
        self._user_repo = user_repo or get_user_identity_repo()

    def track_user(self, chat_id: int, user: ChatUser) -> None:
        """Persist the latest known identity for a Telegram user."""
        self._user_repo.upsert_user(chat_id, user)

    def create_zaruba(
        self,
        chat_id: int,
        time: str,
        creator: ChatUser,
    ) -> ZarubaSession:
        """Create a new zaruba session.

        Args:
            chat_id: The chat ID
            time: The zaruba time
            creator: The Telegram user who created the zaruba

        Returns:
            The created ZarubaSession
        """
        self.track_user(chat_id, creator)
        session = self._session_repo.create_session(
            chat_id=chat_id,
            zaruba_time=time,
            initial_user=creator.display_name,
        )
        self._stats_repo.increment_counter(
            chat_id, creator.display_name, "initiate", user_id=creator.user_id
        )
        self._aura_repo.change_points(
            chat_id, creator.display_name, 200, user_id=creator.user_id
        )
        return session

    def register_user(
        self,
        chat_id: int,
        user: ChatUser,
        time: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Register a user for the zaruba.

        Args:
            chat_id: The chat ID
            user: The Telegram user to register
            time: Optional custom time (uses zaruba time if not provided)

        Returns:
            Tuple of (success, actual_time)

        Raises:
            NoActiveZarubaError: If no active zaruba exists
        """
        self.track_user(chat_id, user)
        session = self._session_repo.get_session(chat_id)
        if session is None:
            raise NoActiveZarubaError()

        reg_time = time or session.zaruba_time
        self._session_repo.register_user(chat_id, user.display_name, reg_time)
        self._stats_repo.increment_counter(
            chat_id, user.display_name, "reg", user_id=user.user_id
        )
        self._aura_repo.change_points(
            chat_id, user.display_name, 100, user_id=user.user_id
        )
        return True, reg_time

    def unregister_user(self, chat_id: int, user: ChatUser) -> bool:
        """Unregister a user from the zaruba.

        Args:
            chat_id: The chat ID
            user: The Telegram user to unregister

        Returns:
            True if user was unregistered, False if not found
        """
        self.track_user(chat_id, user)
        if self._session_repo.unregister_user(chat_id, user.display_name):
            self._stats_repo.increment_counter(
                chat_id, user.display_name, "unreg", user_id=user.user_id
            )
            self._aura_repo.change_points(
                chat_id, user.display_name, -300, user_id=user.user_id
            )
            return True
        return False

    def cancel_zaruba(self, chat_id: int, user: ChatUser) -> bool:
        """Cancel the active zaruba session.

        Args:
            chat_id: The chat ID
            user: The Telegram user canceling

        Returns:
            True if canceled, False if no active session

        Raises:
            NoActiveZarubaError: If no active zaruba exists
        """
        self.track_user(chat_id, user)
        if not self._session_repo.has_active_session(chat_id):
            raise NoActiveZarubaError()

        self._session_repo.delete_session(chat_id)
        self._stats_repo.increment_counter(
            chat_id, user.display_name, "cancel", user_id=user.user_id
        )
        self._aura_repo.change_points(
            chat_id, user.display_name, -500, user_id=user.user_id
        )
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

    def get_user_stats(
        self,
        chat_id: int,
        username: str | None = None,
        user_id: int | None = None,
    ) -> ZarubaStats:
        """Get user statistics.

        Raises:
            StatsNotFoundError: If no stats found for user
        """
        label = username or str(user_id)
        stats = None
        if user_id is not None:
            known_user = self._user_repo.get_by_user_id(chat_id, user_id)
            label = known_user.display_name if known_user else label
            stats = self._stats_repo.get_stats(chat_id, label, user_id=user_id)
            if stats is not None:
                stats.person_name = label
        if stats is None and username is not None:
            known_user = self._user_repo.get_by_username(chat_id, username)
            if known_user is not None:
                label = known_user.display_name
                stats = self._stats_repo.get_stats(
                    chat_id, known_user.display_name, user_id=known_user.user_id
                )
                if stats is not None:
                    stats.person_name = label
            if stats is None:
                stats = self._stats_repo.get_stats(chat_id, username)
        if stats is None:
            raise StatsNotFoundError(label)
        return stats

    def get_user_aura(
        self,
        chat_id: int,
        username: str | None = None,
        user_id: int | None = None,
    ) -> UserAura:
        """Get aura for a user."""
        label = username or str(user_id)
        if user_id is not None:
            known_user = self._user_repo.get_by_user_id(chat_id, user_id)
            label = known_user.display_name if known_user else label
            return self._aura_repo.get_aura(chat_id, label, user_id=user_id)
        if username is not None:
            known_user = self._user_repo.get_by_username(chat_id, username)
            if known_user is not None:
                return self._aura_repo.get_aura(
                    chat_id, known_user.display_name, user_id=known_user.user_id
                )
        return self._aura_repo.get_aura(chat_id, label)

    def get_aura_verdict(self, chat_id: int, aura_points: int) -> str:
        """Get the text verdict for a user's aura in a chat."""
        max_aura = self._aura_repo.get_max_aura_points(chat_id)
        if max_aura is not None and aura_points == max_aura and aura_points > 0:
            return MESSAGES["stats_aura_incredible"]
        if aura_points < 0:
            return MESSAGES["stats_aura_negative"]
        return MESSAGES["stats_aura_positive"]

    def get_aura_verdict_label(self, chat_id: int, aura_points: int) -> str:
        """Get the short aura verdict label for combined stats output."""
        max_aura = self._aura_repo.get_max_aura_points(chat_id)
        if max_aura is not None and aura_points == max_aura and aura_points > 0:
            return MESSAGES["stats_aura_incredible_label"]
        if aura_points < 0:
            return MESSAGES["stats_aura_negative_label"]
        return MESSAGES["stats_aura_positive_label"]

    def apply_absence_penalties(
        self,
        chat_id: int,
        users: list[ChatUser],
    ) -> list[str]:
        """Apply a one-time penalty to users who skipped the active zaruba."""
        session = self._session_repo.get_session(chat_id)
        if session is None:
            return []

        penalized: list[str] = []
        registered_users = set(session.registered_users)
        already_penalized = set(session.absence_penalties)
        for user in users:
            self.track_user(chat_id, user)
            if user.display_name in registered_users or user.display_name in already_penalized:
                continue
            self._aura_repo.change_points(
                chat_id, user.display_name, -5, user_id=user.user_id
            )
            session.absence_penalties.append(user.display_name)
            penalized.append(user.display_name)

        if penalized:
            self._session_repo.save_session(session)

        return penalized

    def register_botinok_vote(
        self,
        chat_id: int,
        voter_username: str,
        target_username: str,
    ) -> Tuple[int, bool, bool]:
        """Register a /botinok vote and fine the target after two unique votes."""
        if self._botinok_repo.has_vote(chat_id, target_username, voter_username):
            current_votes = self._botinok_repo.add_vote(
                chat_id, target_username, voter_username
            )
            return current_votes, False, True

        votes = self._botinok_repo.add_vote(chat_id, target_username, voter_username)

        fine_applied = False
        if votes >= 2:
            target_user = self._user_repo.get_by_username(chat_id, target_username)
            target_user_id = target_user.user_id if target_user else None
            target_name = target_user.display_name if target_user else target_username
            self._aura_repo.change_points(
                chat_id, target_name, -1000, user_id=target_user_id
            )
            self._botinok_repo.clear_votes(chat_id, target_username)
            fine_applied = True

        return votes, fine_applied, False

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
