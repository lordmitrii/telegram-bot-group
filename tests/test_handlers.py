from bot.handlers import get_handlers
from telegram.ext import CommandHandler, MessageHandler

def test_handlers():
    """Ensure all handlers are correctly registered."""
    handlers = get_handlers()
    handler_names = {type(h) for h in handlers}

    assert CommandHandler in handler_names
    assert MessageHandler in handler_names
