"""Tests for the GPT service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.core.config import get_settings
from src.bot.services.gpt import SYSTEM_PROMPT, GPTService


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure settings are re-read for each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_is_configured_false_without_api_key(monkeypatch):
    """Without an API key, the service should report as unconfigured."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    service = GPTService()

    assert service.is_configured is False


def test_is_configured_true_with_api_key(monkeypatch):
    """With an API key set, the service should report as configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    service = GPTService()

    assert service.is_configured is True


@pytest.mark.asyncio
async def test_ask_raises_without_api_key(monkeypatch):
    """Calling ask() without a configured client should raise."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    service = GPTService()

    with pytest.raises(RuntimeError):
        await service.ask("hello")


@pytest.mark.asyncio
async def test_ask_returns_stripped_reply(monkeypatch):
    """ask() should return the trimmed content of the first choice."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    fake_message = MagicMock()
    fake_message.content = "  Hello there!  "
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]

    with patch("src.bot.services.gpt.AsyncOpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)
        mock_openai_cls.return_value = mock_client

        service = GPTService()
        result = await service.ask("Hey how are u?")

    assert result == "Hello there!"
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Hey how are u?"},
        ],
    )
