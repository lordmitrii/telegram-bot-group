"""Shared test fixtures."""

import os
import tempfile

import pytest

from src.bot.core.config import set_db_path
from src.bot.repositories.base import init_db


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
