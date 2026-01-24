"""Tests for base handlers."""

import pytest
from unittest.mock import AsyncMock

from telegram import Message
from telegram.ext import ContextTypes

from src.bot.handlers.base import start, help_command, unknown
from src.bot.i18n.messages import MESSAGES


@pytest.mark.asyncio
async def test_start_command():
    """Test the /start command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await start(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["start"])


@pytest.mark.asyncio
async def test_help_command():
    """Test the /help command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await help_command(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["help"], parse_mode="Markdown")


@pytest.mark.asyncio
async def test_unknown_command():
    """Test an unknown command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.text = "/randomcommand"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await unknown(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["unknown"])
