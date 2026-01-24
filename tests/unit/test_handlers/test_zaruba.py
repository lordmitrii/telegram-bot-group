"""Tests for zaruba handlers."""

import pytest
from unittest.mock import AsyncMock, patch

from telegram import Message, User
from telegram.ext import ContextTypes

import src.bot.handlers.zaruba as zaruba_handlers
from src.bot.i18n.messages import MESSAGES


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the zaruba service before each test."""
    zaruba_handlers._zaruba_service = None
    yield
    zaruba_handlers._zaruba_service = None


@pytest.mark.asyncio
async def test_zaruba_command(test_db):
    """Test /zaruba command initializes registration."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["zaruba_created"].format(time="18:00")
    )


@pytest.mark.asyncio
async def test_zaruba_command_no_time(test_db):
    """Test /zaruba command without time argument."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    await zaruba_handlers.zaruba(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["zaruba_no_time"])


@pytest.mark.asyncio
async def test_reg_command(test_db):
    """Test user registration with /reg command."""
    # First create a zaruba
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    # Now register another user
    update.message.reply_text.reset_mock()
    context.args = []
    update.effective_user.username = "new_user"

    await zaruba_handlers.reg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["reg_success"].format(user="new_user", time="18:00")
    )


@pytest.mark.asyncio
async def test_reg_command_no_zaruba(test_db):
    """Test /reg command when no zaruba exists."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    await zaruba_handlers.reg(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["no_zaruba"])


@pytest.mark.asyncio
async def test_cancel_zaruba(test_db):
    """Test /cancel command resets the event."""
    # First create a zaruba
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    # Now cancel
    update.message.reply_text.reset_mock()

    await zaruba_handlers.cancel_zaruba(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["cancel_success"])


@pytest.mark.asyncio
async def test_unreg(test_db):
    """Test /unreg command allows users to unregister."""
    # First create a zaruba
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    # Now unregister
    update.message.reply_text.reset_mock()

    await zaruba_handlers.unreg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["unreg_success"].format(user="test_user")
    )
