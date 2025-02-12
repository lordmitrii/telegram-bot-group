import pytest
from unittest.mock import AsyncMock
from telegram import Update, User, Message, Chat, ChatMember, Bot
from telegram.ext import ContextTypes
import main  # Import your bot's script

@pytest.mark.asyncio
async def test_start_command():
    """Test the /start command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.text = "/start"
    update.message.reply_text = AsyncMock()
    
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await main.start(update, context)

    update.message.reply_text.assert_called_once_with(
        "Привет! Используйте /zaruba <время> для создания зарубы, /reg для записи, /list для просмотра и /cancel для отмены."
    )

@pytest.mark.asyncio
async def test_zaruba_command():
    """Test /zaruba command initializes registration."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.text = "/zaruba 18:00"
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["18:00"]

    await main.zaruba(update, context)

    update.message.reply_text.assert_called_once_with(
        "🏆 Открывается регистрация на зарубу в 18:00.\nДля записи, напишите /reg <optional: время>"
    )
    assert main.registered_users["test_user"] == "18:00"
    assert main.zaruba_time == "18:00"

@pytest.mark.asyncio
async def test_reg_command():
    """Test user registration with /reg command."""
    main.zaruba_time = "18:00"  # Simulate an active zaruba event
    main.registered_users.clear()

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.text = "/reg"
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    await main.reg(update, context)

    update.message.reply_text.assert_called_once_with("✅ @test_user, вы зарегистрированы на вечернюю зарубу в 18:00!")
    assert main.registered_users["test_user"] == "18:00"

@pytest.mark.asyncio
async def test_list_users():
    """Test /list command lists registered users."""
    main.zaruba_time = "18:00"
    main.registered_users = {"test_user": "18:00"}

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

    await main.list_users(update, context)

    update.message.reply_text.assert_called_once_with(
        "📜 Список участников зарубы:\n✅ @test_user зарегистрирован на 18:00\n❌ @other_user не зарегистрирован\n"
    )

@pytest.mark.asyncio
async def test_cancel_zaruba():
    """Test /cancel command resets the event."""
    main.zaruba_time = "18:00"
    main.registered_users = {"test_user": "18:00"}

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await main.cancel_zaruba(update, context)

    update.message.reply_text.assert_called_once_with("🚫 Заруба отменена. Регистрация закрыта.")
    assert main.zaruba_time is None
    assert main.registered_users == {}

@pytest.mark.asyncio
async def test_unreg():
    """Test /unreg command allows users to unregister."""
    main.registered_users = {"test_user": "18:00"}

    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await main.unreg(update, context)

    update.message.reply_text.assert_called_once_with("🚫 @test_user, вы отменили регистрацию на зарубу.")
    assert "test_user" not in main.registered_users

@pytest.mark.asyncio
async def test_unknown_command():
    """Test an unknown command response."""
    update = AsyncMock()
    update.message = AsyncMock(spec=Message)
    update.message.text = "/randomcommand"
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await main.unknown(update, context)

    update.message.reply_text.assert_called_once_with("❌ Неизвестная команда. Попробуйте /zaruba, /reg, /list или /cancel.")
