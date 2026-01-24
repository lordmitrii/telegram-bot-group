"""Test handler registration."""

from src.bot.handlers import get_handlers
from telegram.ext import CommandHandler, MessageHandler


def test_handlers():
    """Ensure all handlers are correctly registered."""
    handlers = get_handlers()
    handler_names = {type(h) for h in handlers}

    assert CommandHandler in handler_names
    assert MessageHandler in handler_names


def test_handler_count():
    """Ensure correct number of handlers."""
    handlers = get_handlers()
    # 10 command handlers + 1 message handler for unknown
    assert len(handlers) == 11
