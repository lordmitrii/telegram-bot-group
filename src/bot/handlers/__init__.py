"""Handler registration module."""

from typing import List

from telegram.ext import BaseHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.bot.handlers.base import admin_relay_text, beer_check_text, start, help_command, unknown
from src.bot.handlers import football as football_handlers
from src.bot.handlers import zaruba as zaruba_handlers


def get_handlers() -> List[BaseHandler]:
    """Get all bot handlers."""
    return [
        CommandHandler("start", start),
        CommandHandler("zaruba", zaruba_handlers.zaruba),
        CommandHandler("reg", zaruba_handlers.reg),
        CommandHandler("unreg", zaruba_handlers.unreg),
        CommandHandler("list", zaruba_handlers.list_users),
        CommandHandler("cancel", zaruba_handlers.cancel_zaruba),
        CommandHandler("botinok", zaruba_handlers.botinok),
        CommandHandler("help", help_command),
        CommandHandler("subscribe", football_handlers.subscribe),
        CommandHandler("unsubscribe", football_handlers.unsubscribe),
        CommandHandler("stats", zaruba_handlers.zaruba_stats),
        CallbackQueryHandler(
            zaruba_handlers.botinok_callback,
            pattern="^botinok:",
        ),
        CallbackQueryHandler(
            zaruba_handlers.zaruba_callback,
            pattern="^zaruba:",
        ),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_relay_text,
        ),
        MessageHandler(filters.Regex("^Ты в пиве\\?$"), beer_check_text),
        MessageHandler(filters.COMMAND, unknown),
    ]


__all__ = ["get_handlers"]
