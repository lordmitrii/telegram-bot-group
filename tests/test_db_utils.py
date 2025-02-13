import pytest
from bot.db_utils import add_subscriber, remove_subscriber, get_subscribers, init_db
import sqlite3

@pytest.fixture(scope="function")
def setup_db():
    """Sets up an in-memory database for testing."""
    init_db()
    yield
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers")
    conn.commit()
    conn.close()

def test_add_subscriber(setup_db):
    """Test adding a subscriber."""
    add_subscriber(12345)
    subscribers = get_subscribers()
    assert 12345 in subscribers

def test_remove_subscriber(setup_db):
    """Test removing a subscriber."""
    add_subscriber(12345)
    remove_subscriber(12345)
    subscribers = get_subscribers()
    assert 12345 not in subscribers

def test_get_subscribers_empty(setup_db):
    """Test fetching subscribers when none exist."""
    subscribers = get_subscribers()
    assert subscribers == []
