"""Football subscription handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.i18n.messages import MESSAGES
from src.bot.repositories.subscriber import SubscriberRepository

# Repository instance
_subscriber_repo = None


def _get_repo() -> SubscriberRepository:
    """Get or create the subscriber repository instance."""
    global _subscriber_repo
    if _subscriber_repo is None:
        _subscriber_repo = SubscriberRepository()
    return _subscriber_repo


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe command to add chat to subscribers."""
    chat_id = update.effective_chat.id
    _get_repo().add(chat_id)
    await update.message.reply_text(MESSAGES["subscribe"])


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unsubscribe command to remove chat from subscribers."""
    chat_id = update.effective_chat.id
    _get_repo().remove(chat_id)
    await update.message.reply_text(MESSAGES["unsubscribe"])
