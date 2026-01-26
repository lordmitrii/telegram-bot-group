"""Tests for base handlers."""

import pytest
from unittest.mock import AsyncMock

from telegram import Message, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.handlers.base import beer_check_text, start, help_command, unknown
from src.bot.i18n.messages import MESSAGES


@pytest.mark.asyncio
async def test_start_command():
    """Test the /start command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await start(update, context)

    update.message.reply_text.assert_called_once()
    args, kwargs = update.message.reply_text.call_args
    assert args == (MESSAGES["start"],)
    assert isinstance(kwargs.get("reply_markup"), ReplyKeyboardMarkup)
    assert kwargs["reply_markup"].keyboard[0][0].text == MESSAGES["beer_check_button"]


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


@pytest.mark.asyncio
async def test_beer_check_text_default(monkeypatch):
    """Test beer check text handler returns the common reply."""
    monkeypatch.setattr("src.bot.handlers.base.random.random", lambda: 0.5)
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await beer_check_text(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["beer_check_yes"])


@pytest.mark.asyncio
async def test_beer_check_text_rare(monkeypatch):
    """Test beer check text handler returns the rare reply."""
    monkeypatch.setattr("src.bot.handlers.base.random.random", lambda: 0.0)
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await beer_check_text(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["beer_check_no"])
