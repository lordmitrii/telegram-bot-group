from telegram import Update
from telegram.ext import ContextTypes

from bot.db.repositories import add_subscriber, remove_subscriber
from bot.messages import MESSAGES


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /subscribe command to add chat ID to the database."""
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text(MESSAGES["subscribe"])


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /unsubscribe command to remove chat ID from the database."""
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text(MESSAGES["unsubscribe"])
