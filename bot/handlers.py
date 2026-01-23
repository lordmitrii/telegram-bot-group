from telegram.ext import CommandHandler, MessageHandler, filters

from bot.commands.base import start, unknown, help
from bot.commands.zaruba import zaruba, reg, list_users, cancel_zaruba, unreg, zaruba_stats
from bot.commands.football import subscribe, unsubscribe


def get_handlers():
    return [
        CommandHandler('start', start),
        CommandHandler('zaruba', zaruba),
        CommandHandler('reg', reg),
        CommandHandler('unreg', unreg),
        CommandHandler('list', list_users),
        CommandHandler('cancel', cancel_zaruba),
        CommandHandler('help', help),
        CommandHandler('subscribe', subscribe),
        CommandHandler('unsubscribe', unsubscribe),
        CommandHandler('stats', zaruba_stats),
        MessageHandler(filters.COMMAND, unknown),
    ]
