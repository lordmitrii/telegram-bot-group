"""Tests for subscriber repository."""

import pytest

from src.bot.repositories.subscriber import (
    SubscriberRepository,
    add_subscriber,
    get_subscribers,
    remove_subscriber,
)


def test_add_subscriber(test_db):
    """Test adding a subscriber."""
    add_subscriber(12345, db_path=test_db)
    subscribers = get_subscribers(db_path=test_db)
    assert 12345 in subscribers


def test_remove_subscriber(test_db):
    """Test removing a subscriber."""
    add_subscriber(12345, db_path=test_db)
    remove_subscriber(12345, db_path=test_db)
    subscribers = get_subscribers(db_path=test_db)
    assert 12345 not in subscribers


def test_get_subscribers_empty(test_db):
    """Test fetching subscribers when none exist."""
    subscribers = get_subscribers(db_path=test_db)
    assert subscribers == []


def test_subscriber_repository_class(test_db):
    """Test SubscriberRepository class methods."""
    repo = SubscriberRepository(test_db)

    # Test add
    repo.add(99999)
    assert repo.exists(99999)

    # Test get_all
    subscribers = repo.get_all()
    assert len(subscribers) == 1
    assert subscribers[0].chat_id == 99999

    # Test remove
    repo.remove(99999)
    assert not repo.exists(99999)
