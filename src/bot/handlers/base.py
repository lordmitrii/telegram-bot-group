"""Base handlers for start, help, and unknown commands."""

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.i18n.messages import MESSAGES


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(MESSAGES["start"])


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(MESSAGES["help"], parse_mode="Markdown")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text(MESSAGES["unknown"])
