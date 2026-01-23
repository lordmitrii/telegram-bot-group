import pytest
import os, tempfile
from bot.db.repositories import add_subscriber, remove_subscriber, get_subscribers, init_db, change_zarubbl_counter, get_zarubbl_stats
from bot.config import set_db_path
import sqlite3

@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        db_path = tmp.name

    set_db_path(db_path)
    init_db()

    yield db_path

    os.remove(db_path)

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

def test_zarubbl_increase(test_db):
    chat_id = 1
    person_name = "AAA"

    change_zarubbl_counter(person_name=person_name, type="initiate", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="reg", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="cancel", chat_id=chat_id, db_path=test_db)
    change_zarubbl_counter(person_name=person_name, type="unreg", chat_id=chat_id, db_path=test_db)

    stats = get_zarubbl_stats(chat_id=chat_id, person_name=person_name, db_path=test_db)
    assert stats['zarub_canceled'] == 1
    assert stats['zarub_initiated'] == 1
    assert stats['zarub_unreg'] == 1
    assert stats['zarub_reg'] == 1
