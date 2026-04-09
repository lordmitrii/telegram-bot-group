"""Base handlers for start, help, and unknown commands."""

from collections.abc import Awaitable, Callable
from functools import wraps
import random

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.core.config import get_settings
from src.bot.i18n.messages import MESSAGES

CommandHandlerCallback = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def should_skip_command() -> bool:
    """Return whether the command should short-circuit with a funny deferral."""
    return random.random() < 0.1


async def maybe_reply_with_deferral(update: Update) -> bool:
    """Reply with a funny deferral and signal whether command handling should stop."""
    if update.message is None or not should_skip_command():
        return False

    await update.message.reply_text(random.choice(MESSAGES["command_deferrals"]))
    return True


def with_funny_deferral(handler: CommandHandlerCallback) -> CommandHandlerCallback:
    """Wrap a command handler with a small chance to send a funny deferral reply."""

    @wraps(handler)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await maybe_reply_with_deferral(update):
            return
        await handler(update, context)

    return wrapped


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    keyboard = ReplyKeyboardMarkup(
        [[MESSAGES["beer_check_button"]]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    await update.message.reply_text(MESSAGES["start"], reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(MESSAGES["help"], parse_mode="Markdown")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text(MESSAGES["unknown"])


async def beer_check_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle beer check reply keyboard button."""
    if update.message is None:
        return
    reply_text = (
        MESSAGES["beer_check_no"]
        if random.random() < 0.0001
        else MESSAGES["beer_check_yes"]
    )
    await update.message.reply_text(reply_text)


async def admin_relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Relay text from the admin user into the configured admin chat."""
    if update.message is None or update.effective_user is None:
        return
    settings = get_settings()
    if (
        settings.admin_relay_user_id is None
        or settings.admin_relay_chat_id is None
    ):
        return
    if update.effective_user.id != settings.admin_relay_user_id:
        return
    if update.effective_chat is None or update.effective_chat.type != "private":
        await update.message.reply_text(MESSAGES["admin_relay_private_only"])
        return
    if not context.args:
        await update.message.reply_text(MESSAGES["admin_relay_usage"])
        return
    relay_text = " ".join(context.args)

    await context.bot.send_message(
        chat_id=settings.admin_relay_chat_id,
        text=relay_text,
    )
    await update.message.reply_text(MESSAGES["admin_relay_success"])
