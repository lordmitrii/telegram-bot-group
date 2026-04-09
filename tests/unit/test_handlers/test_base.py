"""Tests for base handlers."""

import pytest
from unittest.mock import AsyncMock

from telegram import Message, ReplyKeyboardMarkup, User
from telegram.ext import ContextTypes

from src.bot.handlers.base import (
    admin_relay,
    beer_check_text,
    help_command,
    maybe_reply_with_deferral,
    start,
    unknown,
    with_funny_deferral,
)
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
async def test_maybe_reply_with_deferral_triggers(monkeypatch):
    """Funny deferral should reply and stop command handling."""
    monkeypatch.setattr("src.bot.handlers.base.should_skip_command", lambda: True)
    monkeypatch.setattr("src.bot.handlers.base.random.choice", lambda replies: replies[0])
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    handled = await maybe_reply_with_deferral(update)

    assert handled is True
    update.message.reply_text.assert_called_once_with(MESSAGES["command_deferrals"][0])


@pytest.mark.asyncio
async def test_with_funny_deferral_skips_handler(monkeypatch):
    """Wrapped command should not call the original handler after a deferral."""
    monkeypatch.setattr("src.bot.handlers.base.should_skip_command", lambda: True)
    monkeypatch.setattr("src.bot.handlers.base.random.choice", lambda replies: replies[1])
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    handler = AsyncMock()

    await with_funny_deferral(handler)(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["command_deferrals"][1])
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_with_funny_deferral_calls_handler(monkeypatch):
    """Wrapped command should call the original handler when the deferral does not trigger."""
    monkeypatch.setattr("src.bot.handlers.base.should_skip_command", lambda: False)
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    handler = AsyncMock()

    await with_funny_deferral(handler)(update, context)

    update.message.reply_text.assert_not_called()
    handler.assert_called_once_with(update, context)


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


@pytest.mark.asyncio
async def test_admin_relay_allowed_user_in_private_chat():
    """Admin relay should forward command text only for the configured admin user."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 999001
    update.effective_chat.type = "private"

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["hello", "admins"]
    context.bot.send_message = AsyncMock()

    await admin_relay(update, context)

    context.bot.send_message.assert_called_once_with(
        chat_id=-100999001,
        text="hello admins",
    )
    update.message.reply_text.assert_called_once_with(MESSAGES["admin_relay_success"])


@pytest.mark.asyncio
async def test_admin_relay_ignores_other_users():
    """Relay should not run for non-admin users."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 123
    update.effective_chat.type = "private"

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["hello", "admins"]
    context.bot.send_message = AsyncMock()

    await admin_relay(update, context)

    context.bot.send_message.assert_not_called()
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_admin_relay_disabled_without_env(monkeypatch):
    """Relay should be disabled when admin relay env vars are not configured."""
    from src.bot.core.config import get_settings

    monkeypatch.delenv("ADMIN_RELAY_USER_ID", raising=False)
    monkeypatch.delenv("ADMIN_RELAY_CHAT_ID", raising=False)
    get_settings.cache_clear()
    try:
        update = AsyncMock()
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.effective_user = AsyncMock(spec=User)
        update.effective_user.id = 999001
        update.effective_chat.type = "private"

        context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["hello", "admins"]
        context.bot.send_message = AsyncMock()

        await admin_relay(update, context)

        context.bot.send_message.assert_not_called()
        update.message.reply_text.assert_not_called()
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_admin_relay_private_only():
    """Relay command should only work in private chat."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 999001
    update.effective_chat.type = "group"

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["hello", "admins"]
    context.bot.send_message = AsyncMock()

    await admin_relay(update, context)

    context.bot.send_message.assert_not_called()
    update.message.reply_text.assert_called_once_with(MESSAGES["admin_relay_private_only"])


@pytest.mark.asyncio
async def test_admin_relay_requires_text():
    """Relay command should require text after /relay."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 999001
    update.effective_chat.type = "private"

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot.send_message = AsyncMock()

    await admin_relay(update, context)

    context.bot.send_message.assert_not_called()
    update.message.reply_text.assert_called_once_with(MESSAGES["admin_relay_usage"])
