"""Tests for the mention-reply handler."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Message, MessageEntity, Update
from telegram.ext import ContextTypes

import src.bot.handlers.mention as mention_handlers
from src.bot.i18n.messages import MESSAGES


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the shared GPT service before each test."""
    mention_handlers._gpt_service = None
    yield
    mention_handlers._gpt_service = None


def make_update(text: str, mention: str = "@test_bot") -> AsyncMock:
    offset = text.index(mention)
    entity = MessageEntity(type=MessageEntity.MENTION, offset=offset, length=len(mention))

    update = AsyncMock(spec=Update)
    update.message = AsyncMock(spec=Message)
    update.message.text = text
    update.message.entities = [entity]
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 123456
    return update


def make_context() -> AsyncMock:
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.username = "test_bot"
    context.bot.send_chat_action = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_mention_without_entities_is_ignored():
    """A message with no entities should not trigger a reply."""
    update = make_update("@test_bot Hey how are u?")
    update.message.entities = []
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_mention_of_someone_else_is_ignored():
    """A mention entity that isn't the bot's own username should not trigger a reply."""
    update = make_update("@someone_else Hey how are u?", mention="@someone_else")
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_mention_not_configured_is_ignored(monkeypatch):
    """When no OpenAI key is configured, the handler should not reply."""
    fake_service = MagicMock()
    fake_service.is_configured = False
    monkeypatch.setattr(mention_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("@test_bot Hey how are u?")
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_mention_replies_with_gpt_response(monkeypatch):
    """A mention with a configured service should reply with the GPT response."""
    fake_service = MagicMock()
    fake_service.is_configured = True
    fake_service.ask = AsyncMock(return_value="I'm doing great, thanks!")
    monkeypatch.setattr(mention_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("@test_bot Hey how are u?")
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    fake_service.ask.assert_called_once_with("Hey how are u?")
    context.bot.send_chat_action.assert_called_once()
    update.message.reply_text.assert_called_once_with("I'm doing great, thanks!")


@pytest.mark.asyncio
async def test_mention_with_only_the_mention_is_ignored(monkeypatch):
    """A mention with no other text should not call GPT or reply."""
    fake_service = MagicMock()
    fake_service.is_configured = True
    fake_service.ask = AsyncMock()
    monkeypatch.setattr(mention_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("@test_bot")
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    fake_service.ask.assert_not_called()
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_mention_gpt_failure_replies_with_error(monkeypatch):
    """A GPT failure should reply with a friendly error instead of raising."""
    fake_service = MagicMock()
    fake_service.is_configured = True
    fake_service.ask = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(mention_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("@test_bot Hey how are u?")
    context = make_context()

    await mention_handlers.mention_reply(update, context)

    update.message.reply_text.assert_called_once_with(MESSAGES["gpt_error"])
