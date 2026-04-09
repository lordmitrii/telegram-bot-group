"""Handler registration module."""

from typing import List

from telegram.ext import BaseHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.bot.handlers.base import (
    admin_relay,
    beer_check_text,
    help_command,
    start,
    unknown,
    with_funny_deferral,
)
from src.bot.handlers import football as football_handlers
from src.bot.handlers import zaruba as zaruba_handlers


def get_handlers() -> List[BaseHandler]:
    """Get all bot handlers."""
    return [
        CommandHandler("start", start),
        CommandHandler("zaruba", with_funny_deferral(zaruba_handlers.zaruba)),
        CommandHandler("reg", with_funny_deferral(zaruba_handlers.reg)),
        CommandHandler("unreg", with_funny_deferral(zaruba_handlers.unreg)),
        CommandHandler("list", with_funny_deferral(zaruba_handlers.list_users)),
        CommandHandler("cancel", with_funny_deferral(zaruba_handlers.cancel_zaruba)),
        CommandHandler("botinok", with_funny_deferral(zaruba_handlers.botinok)),
        CommandHandler("relay", with_funny_deferral(admin_relay)),
        CommandHandler("help", with_funny_deferral(help_command)),
        CommandHandler("subscribe", football_handlers.subscribe),
        CommandHandler("unsubscribe", football_handlers.unsubscribe),
        CommandHandler("stats", with_funny_deferral(zaruba_handlers.zaruba_stats)),
        CallbackQueryHandler(
            zaruba_handlers.botinok_callback,
            pattern="^botinok:",
        ),
        CallbackQueryHandler(
            zaruba_handlers.zaruba_callback,
            pattern="^zaruba:",
        ),
        MessageHandler(filters.Regex("^Ты в пиве\\?$"), beer_check_text),
        MessageHandler(filters.COMMAND, unknown),
    ]


__all__ = ["get_handlers"]
