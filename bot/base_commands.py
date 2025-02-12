import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.messages import MESSAGES  

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Introduction command."""
    await update.message.reply_text(MESSAGES["start"])

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays available commands."""
    await update.message.reply_text(MESSAGES["help"], parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    await update.message.reply_text(MESSAGES["unknown"])
