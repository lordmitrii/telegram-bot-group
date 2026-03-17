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
    update.effective_user.id = 1
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    args, kwargs = update.message.reply_text.call_args
    assert MESSAGES["zaruba_created"].format(time="18:00") in args[0]
    assert MESSAGES["list_registered"] in args[0]
    assert "@test_user" in args[0]
    assert kwargs["reply_markup"] is not None
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_zaruba_command_no_time(test_db):
    """Test /zaruba command without time argument."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
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
    update.effective_user.id = 1
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
    update.effective_user.id = 2

    await zaruba_handlers.reg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["reg_success"].format(user="new_user", time="18:00")
    )


@pytest.mark.asyncio
async def test_reg_command_already_registered(test_db):
    """Test /reg command when user is already registered."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    update.message.reply_text.reset_mock()
    context.args = []

    await zaruba_handlers.reg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["reg_already_registered"].format(user="test_user")
    )


@pytest.mark.asyncio
async def test_reg_command_no_zaruba(test_db):
    """Test /reg command when no zaruba exists."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
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
    update.effective_user.id = 1
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
    update.effective_user.id = 1
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    update.message.reply_text.reset_mock()
    update.effective_user.id = 2
    update.effective_user.username = "other_user"
    context.args = []

    await zaruba_handlers.reg(update, context)

    # Now unregister
    update.message.reply_text.reset_mock()

    await zaruba_handlers.unreg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["unreg_success"].format(user="other_user")
    )


@pytest.mark.asyncio
async def test_unreg_creator_forbidden(test_db):
    """Test /unreg command does not let the creator unreg."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    update.message.reply_text.reset_mock()
    context.args = []

    await zaruba_handlers.unreg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["unreg_creator_forbidden"].format(user="test_user")
    )


@pytest.mark.asyncio
async def test_botinok_vote_and_fine(test_db):
    """Two users voting with /botinok should fine the target."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "creator"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["@target"]
    update.effective_user.username = "voter1"
    update.effective_user.id = 2

    await zaruba_handlers.botinok(update, context)

    args, kwargs = update.message.reply_text.call_args
    assert args == (MESSAGES["botinok_vote"].format(target="target", votes=1),)
    assert kwargs["reply_markup"] is not None

    update.message.reply_text.reset_mock()
    update.effective_user.username = "voter2"
    update.effective_user.id = 3

    await zaruba_handlers.botinok(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["botinok_fined"].format(target="target")
    )

    update.message.reply_text.reset_mock()

    await zaruba_handlers.botinok(update, context)

    args, kwargs = update.message.reply_text.call_args
    assert args == (MESSAGES["botinok_vote"].format(target="target", votes=1),)
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_botinok_callback_fines_and_edits_message(test_db):
    """Inline botinok button should allow the second vote without typing the command again."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "creator"
    update.effective_user.first_name = "Creator"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["@target"]
    update.effective_user.id = 2
    update.effective_user.username = "voter1"
    update.effective_user.first_name = "Voter1"

    await zaruba_handlers.botinok(update, context)

    callback_update = AsyncMock()
    callback_update.effective_chat.id = 123456
    callback_update.effective_user = AsyncMock(spec=User)
    callback_update.effective_user.id = 3
    callback_update.effective_user.username = "voter2"
    callback_update.effective_user.first_name = "Voter2"
    callback_update.callback_query = AsyncMock()
    callback_update.callback_query.data = "botinok:target"
    callback_update.callback_query.answer = AsyncMock()
    callback_update.callback_query.edit_message_text = AsyncMock()

    await zaruba_handlers.botinok_callback(callback_update, context)

    callback_update.callback_query.answer.assert_called_once_with()
    callback_update.callback_query.edit_message_text.assert_called_once_with(
        MESSAGES["botinok_fined"].format(target="target")
    )


@pytest.mark.asyncio
async def test_zaruba_callback_reg(test_db):
    """Inline zaruba register button should register without typing /reg."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "creator"
    update.effective_user.first_name = "Creator"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    callback_update = AsyncMock()
    callback_update.effective_chat.id = 123456
    callback_update.effective_user = AsyncMock(spec=User)
    callback_update.effective_user.id = 2
    callback_update.effective_user.username = "new_user"
    callback_update.effective_user.first_name = "New"
    callback_update.callback_query = AsyncMock()
    callback_update.callback_query.data = "zaruba:reg"
    callback_update.callback_query.answer = AsyncMock()
    callback_update.callback_query.message = AsyncMock(spec=Message)
    callback_update.callback_query.edit_message_text = AsyncMock()

    await zaruba_handlers.zaruba_callback(callback_update, context)

    callback_update.callback_query.answer.assert_called_once_with()
    args, kwargs = callback_update.callback_query.edit_message_text.call_args
    assert MESSAGES["zaruba_created"].format(time="18:00") in args[0]
    assert "@creator" in args[0]
    assert "@new_user" in args[0]
    assert kwargs["reply_markup"] is not None
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_zaruba_callback_cancel_removes_buttons(test_db):
    """Inline zaruba cancel button should cancel and clear inline markup."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 1
    update.effective_user.username = "creator"
    update.effective_user.first_name = "Creator"
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await zaruba_handlers.zaruba(update, context)

    callback_update = AsyncMock()
    callback_update.effective_chat.id = 123456
    callback_update.effective_user = AsyncMock(spec=User)
    callback_update.effective_user.id = 1
    callback_update.effective_user.username = "creator"
    callback_update.effective_user.first_name = "Creator"
    callback_update.callback_query = AsyncMock()
    callback_update.callback_query.data = "zaruba:cancel"
    callback_update.callback_query.answer = AsyncMock()
    callback_update.callback_query.edit_message_text = AsyncMock()
    callback_update.callback_query.message = AsyncMock(spec=Message)

    await zaruba_handlers.zaruba_callback(callback_update, context)

    callback_update.callback_query.answer.assert_called_once_with()
    callback_update.callback_query.edit_message_text.assert_called_once_with(
        MESSAGES["cancel_success"]
    )
