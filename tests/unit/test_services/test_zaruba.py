"""Tests for zaruba service."""

import pytest

from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.models.zaruba import ZarubaStats
from src.bot.repositories.session import SessionRepository
from src.bot.repositories.zaruba import ZarubaStatsRepository
from src.bot.services.zaruba import ZarubaService


def test_create_zaruba(test_db):
    """Test creating a zaruba session."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    session = service.create_zaruba(chat_id=123, time="18:00", creator_username="test_user")

    assert session.chat_id == 123
    assert session.zaruba_time == "18:00"
    assert "test_user" in session.registered_users


def test_register_user(test_db):
    """Test registering a user for zaruba."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    service.create_zaruba(chat_id=123, time="18:00", creator_username="creator")
    success, reg_time = service.register_user(chat_id=123, username="new_user")

    assert success
    assert reg_time == "18:00"


def test_register_user_custom_time(test_db):
    """Test registering with custom time."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    service.create_zaruba(chat_id=123, time="18:00", creator_username="creator")
    success, reg_time = service.register_user(chat_id=123, username="new_user", time="19:00")

    assert success
    assert reg_time == "19:00"


def test_register_user_no_session(test_db):
    """Test registering when no session exists."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    with pytest.raises(NoActiveZarubaError):
        service.register_user(chat_id=123, username="new_user")


def test_unregister_user(test_db):
    """Test unregistering a user."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    service.create_zaruba(chat_id=123, time="18:00", creator_username="test_user")
    result = service.unregister_user(chat_id=123, username="test_user")

    assert result


def test_unregister_user_not_registered(test_db):
    """Test unregistering a user who is not registered."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    service.create_zaruba(chat_id=123, time="18:00", creator_username="creator")
    result = service.unregister_user(chat_id=123, username="nonexistent")

    assert not result


def test_cancel_zaruba(test_db):
    """Test canceling a zaruba session."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    service.create_zaruba(chat_id=123, time="18:00", creator_username="creator")
    result = service.cancel_zaruba(chat_id=123, username="creator")

    assert result
    assert service.get_session(123) is None


def test_cancel_zaruba_no_session(test_db):
    """Test canceling when no session exists."""
    session_repo = SessionRepository(test_db)
    stats_repo = ZarubaStatsRepository(test_db)
    service = ZarubaService(session_repo=session_repo, stats_repo=stats_repo)

    with pytest.raises(NoActiveZarubaError):
        service.cancel_zaruba(chat_id=123, username="creator")


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
