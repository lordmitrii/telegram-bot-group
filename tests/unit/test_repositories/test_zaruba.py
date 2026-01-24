"""Tests for zaruba repository."""

import pytest

from src.bot.repositories.zaruba import (
    ZarubaStatsRepository,
    change_zarubbl_counter,
    get_zarubbl_stats,
)


def test_zarubbl_increase(test_db):
    """Test incrementing zaruba counters."""
    chat_id = 1
    person_name = "AAA"

    change_zarubbl_counter(person_name=person_name, type="initiate", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="reg", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="cancel", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="unreg", chat_id=chat_id, db_path=test_db)

    stats = get_zarubbl_stats(chat_id=chat_id, person_name=person_name, db_path=test_db)
    assert stats["zarub_canceled"] == 1
    assert stats["zarub_initiated"] == 1
    assert stats["zarub_unreg"] == 1
    assert stats["zarub_reg"] == 1


def test_zaruba_stats_repository_class(test_db):
    """Test ZarubaStatsRepository class methods."""
    repo = ZarubaStatsRepository(test_db)

    # Initially no stats
    stats = repo.get_stats(chat_id=100, person_name="test_user")
    assert stats is None

    # Increment a counter
    repo.increment_counter(chat_id=100, person_name="test_user", counter_type="initiate")
    stats = repo.get_stats(chat_id=100, person_name="test_user")
    assert stats is not None
    assert stats.zarub_initiated == 1
    assert stats.zarub_reg == 0


def test_zaruba_stats_not_found(test_db):
    """Test getting stats for non-existent user."""
    with pytest.raises(IndexError):
        get_zarubbl_stats(chat_id=999, person_name="nonexistent", db_path=test_db)
