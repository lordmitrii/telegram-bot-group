"""Test handler registration."""

from src.bot.handlers import get_handlers
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler


def test_handlers():
    """Ensure all handlers are correctly registered."""
    handlers = get_handlers()
    handler_names = {type(h) for h in handlers}

    assert CommandHandler in handler_names
    assert CallbackQueryHandler in handler_names
    assert MessageHandler in handler_names


def test_handler_count():
    """Ensure correct number of handlers."""
    handlers = get_handlers()
    # 11 command handlers + 2 callback handlers + 1 beer check message handler + 1 unknown handler
    assert len(handlers) == 15
