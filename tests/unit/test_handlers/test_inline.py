"""Tests for the inline mode handler."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import InlineQuery, Update
from telegram.ext import ContextTypes

import src.bot.handlers.inline as inline_handlers
from src.bot.i18n.messages import MESSAGES


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the shared GPT service before each test."""
    inline_handlers._gpt_service = None
    yield
    inline_handlers._gpt_service = None


def make_update(query_text: str) -> AsyncMock:
    update = AsyncMock(spec=Update)
    update.inline_query = AsyncMock(spec=InlineQuery)
    update.inline_query.query = query_text
    update.inline_query.answer = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_inline_query_empty_text_answers_nothing():
    """An empty/whitespace query should answer with no results without calling GPT."""
    update = make_update("   ")
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await inline_handlers.inline_query(update, context)

    update.inline_query.answer.assert_called_once_with([], cache_time=0)


@pytest.mark.asyncio
async def test_inline_query_not_configured_answers_nothing(monkeypatch):
    """When no OpenAI key is configured, the handler should answer with no results."""
    fake_service = MagicMock()
    fake_service.is_configured = False
    monkeypatch.setattr(inline_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("Hey how are u?")
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await inline_handlers.inline_query(update, context)

    update.inline_query.answer.assert_called_once_with([], cache_time=0)


@pytest.mark.asyncio
async def test_inline_query_answers_with_gpt_response(monkeypatch):
    """A configured service should answer with an article containing the GPT reply."""
    fake_service = MagicMock()
    fake_service.is_configured = True
    fake_service.ask = AsyncMock(return_value="I'm doing great, thanks!")
    monkeypatch.setattr(inline_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("Hey how are u?")
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await inline_handlers.inline_query(update, context)

    fake_service.ask.assert_called_once_with("Hey how are u?")
    update.inline_query.answer.assert_called_once()
    args, kwargs = update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 1
    assert results[0].title == MESSAGES["inline_gpt_title"]
    assert results[0].input_message_content.message_text == "I'm doing great, thanks!"
    assert kwargs == {"cache_time": 0}


@pytest.mark.asyncio
async def test_inline_query_gpt_failure_answers_with_error(monkeypatch):
    """A GPT failure should answer with a friendly error result instead of raising."""
    fake_service = MagicMock()
    fake_service.is_configured = True
    fake_service.ask = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(inline_handlers, "get_gpt_service", lambda: fake_service)

    update = make_update("Hey how are u?")
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    await inline_handlers.inline_query(update, context)

    update.inline_query.answer.assert_called_once()
    args, kwargs = update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 1
    assert results[0].title == MESSAGES["inline_gpt_error"]
    assert kwargs == {"cache_time": 0}
