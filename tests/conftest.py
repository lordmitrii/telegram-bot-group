"""Shared test fixtures."""

import os
import tempfile

import pytest

from src.bot.core.config import get_settings, set_db_path
from src.bot.repositories.base import init_db


@pytest.fixture(scope="session", autouse=True)
def test_env():
    """Ensure required settings are present for test runs."""
    original_token = os.environ.get("TOKEN")
    original_admin_relay_user_id = os.environ.get("ADMIN_RELAY_USER_ID")
    original_admin_relay_chat_id = os.environ.get("ADMIN_RELAY_CHAT_ID")
    os.environ.setdefault("TOKEN", "test-token")
    os.environ.setdefault("ADMIN_RELAY_USER_ID", "999001")
    os.environ.setdefault("ADMIN_RELAY_CHAT_ID", "-100999001")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    if original_token is None:
        os.environ.pop("TOKEN", None)
    else:
        os.environ["TOKEN"] = original_token
    if original_admin_relay_user_id is None:
        os.environ.pop("ADMIN_RELAY_USER_ID", None)
    else:
        os.environ["ADMIN_RELAY_USER_ID"] = original_admin_relay_user_id
    if original_admin_relay_chat_id is None:
        os.environ.pop("ADMIN_RELAY_CHAT_ID", None)
    else:
        os.environ["ADMIN_RELAY_CHAT_ID"] = original_admin_relay_chat_id


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        db_path = tmp.name

    set_db_path(db_path)
    init_db(db_path)

    yield db_path

    os.remove(db_path)


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    from unittest.mock import AsyncMock
    from telegram import Message, User

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 42
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_chat.id = 123456

    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    from unittest.mock import AsyncMock
    from telegram.ext import ContextTypes

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    return context
