from telegram.ext import CommandHandler, MessageHandler, filters
from bot.base_commands import start, unknown, help
from bot.zaruba_commands import  zaruba, reg, list_users, cancel_zaruba, unreg
from bot.football_updates import subscribe, unsubscribe


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
        MessageHandler(filters.COMMAND, unknown),
    ]
