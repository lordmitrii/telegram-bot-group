"""Tests for zaruba service."""

import pytest

from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.models.user import ChatUser
from src.bot.models.zaruba import ZarubaStats
from src.bot.repositories.aura import AuraRepository
from src.bot.repositories.session import SessionRepository
from src.bot.repositories.user_identity import UserIdentityRepository
from src.bot.repositories.zaruba import ZarubaStatsRepository
from src.bot.services.zaruba import ZarubaService


def make_user(user_id: int, name: str) -> ChatUser:
    """Create a stable chat user for tests."""
    return ChatUser(user_id=user_id, display_name=name, username=name)


def test_create_zaruba(test_db):
    """Test creating a zaruba session."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    user_repo = UserIdentityRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=user_repo,
    )

    session = service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "test_user"))

    assert session.chat_id == 123
    assert session.zaruba_time == "18:00"
    assert "test_user" in session.registered_users
    assert service.get_user_aura(123, user_id=1, username="test_user").aura_points == 200


def test_register_user(test_db):
    """Test registering a user for zaruba."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))
    success, reg_time = service.register_user(chat_id=123, user=make_user(2, "new_user"))

    assert success
    assert reg_time == "18:00"
    assert service.get_user_aura(123, user_id=2, username="new_user").aura_points == 100


def test_register_user_custom_time(test_db):
    """Test registering with custom time."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))
    success, reg_time = service.register_user(
        chat_id=123, user=make_user(2, "new_user"), time="19:00"
    )

    assert success
    assert reg_time == "19:00"
    assert service.get_user_aura(123, user_id=2, username="new_user").aura_points == 100


def test_register_user_no_session(test_db):
    """Test registering when no session exists."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    with pytest.raises(NoActiveZarubaError):
        service.register_user(chat_id=123, user=make_user(2, "new_user"))


def test_unregister_user(test_db):
    """Test unregistering a user."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "test_user"))
    result = service.unregister_user(chat_id=123, user=make_user(1, "test_user"))

    assert result
    assert service.get_user_aura(123, user_id=1, username="test_user").aura_points == -100


def test_unregister_user_not_registered(test_db):
    """Test unregistering a user who is not registered."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))
    result = service.unregister_user(chat_id=123, user=make_user(2, "nonexistent"))

    assert not result


def test_cancel_zaruba(test_db):
    """Test canceling a zaruba session."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))
    result = service.cancel_zaruba(chat_id=123, user=make_user(1, "creator"))

    assert result
    assert service.get_session(123) is None
    assert service.get_user_aura(123, user_id=1, username="creator").aura_points == -300


def test_cancel_zaruba_no_session(test_db):
    """Test canceling when no session exists."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    with pytest.raises(NoActiveZarubaError):
        service.cancel_zaruba(chat_id=123, user=make_user(1, "creator"))


def test_apply_absence_penalties_once_per_session(test_db):
    """Users who skip a zaruba should only be penalized once per session."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))

    penalized = service.apply_absence_penalties(
        123, [make_user(1, "creator"), make_user(2, "lazy_user")]
    )
    penalized_again = service.apply_absence_penalties(
        123, [make_user(1, "creator"), make_user(2, "lazy_user")]
    )

    assert penalized == ["lazy_user"]
    assert penalized_again == []
    assert service.get_user_aura(123, user_id=2, username="lazy_user").aura_points == -5


def test_botinok_requires_two_unique_votes(test_db):
    """A user should be fined after two unique /botinok votes."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=UserIdentityRepository(test_db),
    )

    service.create_zaruba(chat_id=123, time="18:00", creator=make_user(1, "creator"))
    service.track_user(123, make_user(10, "target"))

    votes, fine_applied, already_voted = service.register_botinok_vote(123, "voter1", "target")
    assert (votes, fine_applied, already_voted) == (1, False, False)
    assert service.get_user_aura(123, user_id=10, username="target").aura_points == 0

    votes, fine_applied, already_voted = service.register_botinok_vote(123, "voter2", "target")
    assert (votes, fine_applied, already_voted) == (2, True, False)
    assert service.get_user_aura(123, user_id=10, username="target").aura_points == -1000

    votes, fine_applied, already_voted = service.register_botinok_vote(123, "voter2", "target")
    assert (votes, fine_applied, already_voted) == (2, False, True)


def test_stats_and_aura_persist_across_username_change(test_db):
    """Stats and aura should stay attached to the Telegram user ID."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    aura_repo = AuraRepository(test_db)
    user_repo = UserIdentityRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=stats_repo,
        aura_repo=aura_repo,
        user_repo=user_repo,
    )

    old_user = make_user(77, "old_name")
    new_user = make_user(77, "new_name")

    service.create_zaruba(chat_id=123, time="18:00", creator=old_user)
    service.cancel_zaruba(chat_id=123, user=old_user)
    service.track_user(123, new_user)

    stats = service.get_user_stats(123, user_id=77, username="new_name")
    aura = service.get_user_aura(123, user_id=77, username="new_name")

    assert stats.person_name == "new_name"
    assert stats.zarub_initiated == 1
    assert stats.zarub_canceled == 1
    assert aura.aura_points == -300


def test_evaluate_user_reliability_good():
    """Test reliability evaluation for good user."""
    service = ZarubaService()
    stats = ZarubaStats(
        person_name="good_user",
        chat_id=123,
        zarub_initiated=10,
        zarub_reg=10,
        zarub_canceled=1,
        zarub_unreg=1,
    )

    is_reliable, chance = service.evaluate_user_reliability(stats)

    assert is_reliable
    assert chance == 10.0  # (1+1)/(10+10) = 0.1 = 10%


def test_evaluate_user_reliability_bad():
    """Test reliability evaluation for unreliable user."""
    service = ZarubaService()
    stats = ZarubaStats(
        person_name="bad_user",
        chat_id=123,
        zarub_initiated=5,
        zarub_reg=5,
        zarub_canceled=3,
        zarub_unreg=3,
    )

    is_reliable, chance = service.evaluate_user_reliability(stats)

    assert not is_reliable
    assert chance == 60.0  # (3+3)/(5+5) = 0.6 = 60%
