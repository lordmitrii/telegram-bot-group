"""Zaruba command handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.i18n.messages import MESSAGES
from src.bot.services.zaruba import ZarubaService

# Service instance (will be initialized on first use)
_zaruba_service = None


def _get_service() -> ZarubaService:
    """Get or create the zaruba service instance."""
    global _zaruba_service
    if _zaruba_service is None:
        _zaruba_service = ZarubaService()
    return _zaruba_service


def _get_username(update: Update) -> str | None:
    """Get username from update, falling back to first_name."""
    user = update.effective_user
    return user.username or user.first_name if user else None


async def zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /zaruba command to create a new event."""
    username = _get_username(update)
    if not username:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    if not context.args:
        await update.message.reply_text(MESSAGES["zaruba_no_time"])
        return

    time = " ".join(context.args)
    chat_id = update.effective_chat.id

    service = _get_service()
    service.create_zaruba(chat_id, time, username)

    await update.message.reply_text(MESSAGES["zaruba_created"].format(time=time))


async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reg command to register for an event."""
    username = _get_username(update)
    if not username:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    chat_id = update.effective_chat.id
    custom_time = " ".join(context.args) if context.args else None

    service = _get_service()
    try:
        _, reg_time = service.register_user(chat_id, username, custom_time)
        await update.message.reply_text(
            MESSAGES["reg_success"].format(user=username, time=reg_time)
        )
    except NoActiveZarubaError:
        await update.message.reply_text(MESSAGES["no_zaruba"])


async def unreg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unreg command to unregister from an event."""
    username = _get_username(update)
    if not username:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    chat_id = update.effective_chat.id

    service = _get_service()
    if service.unregister_user(chat_id, username):
        await update.message.reply_text(
            MESSAGES["unreg_success"].format(user=username)
        )
    else:
        await update.message.reply_text(
            MESSAGES["unreg_not_found"].format(user=username)
        )


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command to show registered users."""
    chat_id = update.effective_chat.id

    service = _get_service()
    session = service.get_session(chat_id)

    if session is None:
        await update.message.reply_text(MESSAGES["list_no_zaruba"])
        return

    # Get chat administrators
    try:
        bot_username = context.bot.username
        members = await context.bot.get_chat_administrators(chat_id)
        member_usernames = [
            m.user.username or m.user.first_name
            for m in members
            if m.user.username != bot_username
        ]
    except Exception:
        await update.message.reply_text(MESSAGES["list_members_error"])
        return

    if not member_usernames:
        await update.message.reply_text(MESSAGES["list_members_error"])
        return

    registered_users = session.registered_users
    response_text = f"{MESSAGES['list_registered']}\n"

    for username in member_usernames:
        if username in registered_users:
            response_text += MESSAGES["list_reg_yes"].format(
                user=username, time=registered_users[username]
            )
        else:
            response_text += MESSAGES["list_reg_no"].format(user=username)

    await update.message.reply_text(response_text, parse_mode="Markdown")


async def cancel_zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command to cancel an event."""
    username = _get_username(update)
    chat_id = update.effective_chat.id

    service = _get_service()
    try:
        service.cancel_zaruba(chat_id, username or "unknown")
        await update.message.reply_text(MESSAGES["cancel_success"])
    except NoActiveZarubaError:
        await update.message.reply_text(MESSAGES["no_zaruba"])


async def zaruba_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command to show user statistics."""
    chat_id = update.effective_chat.id
    args = context.args

    try:
        if args:
            username = args[0].lstrip("@")
        else:
            username = update.effective_user.username
            if not username:
                await update.message.reply_text(MESSAGES["stats_user_invalid"])
                return
    except Exception:
        await update.message.reply_text(MESSAGES["stats_user_invalid"])
        return

    service = _get_service()
    try:
        stats = service.get_user_stats(chat_id, username)
    except StatsNotFoundError:
        await update.message.reply_text(MESSAGES["stats_not_found"].format(user=username))
        return

    await update.message.reply_text(
        MESSAGES["list_stats"].format(
            user=username,
            initiated=stats.zarub_initiated,
            canceled=stats.zarub_canceled,
            regnuto=stats.zarub_reg,
            unregnuto=stats.zarub_unreg,
        ),
        parse_mode="Markdown",
    )

    is_reliable, chance = service.evaluate_user_reliability(stats)

    if is_reliable:
        await update.message.reply_text(
            MESSAGES["stats_good"].format(chance=chance), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            MESSAGES["stats_bad"].format(chance=chance), parse_mode="Markdown"
        )
