import pytest
from unittest.mock import AsyncMock
from telegram import Update, User, Message, Chat, ChatMember, Bot
from telegram.ext import ContextTypes
from bot import zaruba_commands
from bot.messages import MESSAGES

@pytest.mark.asyncio
async def test_zaruba_command():
    """Test /zaruba command initializes registration."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    # Reset state before test
    zaruba_commands.zaruba_time = None
    zaruba_commands.registered_users.clear()

    await zaruba_commands.zaruba(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["zaruba_created"].format(time="18:00")
    )
    assert zaruba_commands.registered_users["test_user"] == "18:00"
    assert zaruba_commands.zaruba_time == "18:00"

@pytest.mark.asyncio
async def test_reg_command():
    """Test user registration with /reg command."""
    zaruba_commands.zaruba_time = "18:00"
    zaruba_commands.registered_users.clear()

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    await zaruba_commands.reg(update, context)

    update.message.reply_text.assert_called_once_with(
        MESSAGES["reg_success"].format(user="test_user", time="18:00")
    )
    assert zaruba_commands.registered_users["test_user"] == "18:00"

@pytest.mark.asyncio
async def test_list_users():
    """Test /list command lists registered users."""
    zaruba_commands.zaruba_time = "18:00"
    zaruba_commands.registered_users = {"test_user": "18:00"}

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_chat = AsyncMock(spec=Chat)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock(spec=Bot)
    context.bot.username = "test_bot"
    context.bot.get_chat.return_value = AsyncMock(spec=Chat)
    context.bot.get_chat_administrators.return_value = [
        AsyncMock(spec=ChatMember, user=AsyncMock(spec=User, username="test_user")),
        AsyncMock(spec=ChatMember, user=AsyncMock(spec=User, username="other_user"))
    ]

    await zaruba_commands.list_users(update, context)

    expected_message = f"{MESSAGES['list_registered']}\n✅ @test_user - 18:00\n"
    update.message.reply_text.assert_called_once_with(expected_message, parse_mode="Markdown")

@pytest.mark.asyncio
async def test_cancel_zaruba():
    """Test /cancel command resets the event."""
    zaruba_commands.zaruba_time = "18:00"
    zaruba_commands.registered_users = {"test_user": "18:00"}

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await zaruba_commands.cancel_zaruba(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["cancel_success"])
    assert zaruba_commands.zaruba_time is None
    assert zaruba_commands.registered_users == {}

@pytest.mark.asyncio
async def test_unreg():
    """Test /unreg command allows users to unregister."""
    zaruba_commands.registered_users = {"test_user": "18:00"}

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await zaruba_commands.unreg(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["unreg_success"].format(user="test_user"))
    assert "test_user" not in zaruba_commands.registered_users
