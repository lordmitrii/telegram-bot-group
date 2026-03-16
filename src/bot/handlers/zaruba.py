"""Zaruba command handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.i18n.messages import MESSAGES
from src.bot.models.user import ChatUser
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


def _get_chat_user(update: Update) -> ChatUser | None:
    """Build a stable chat user object from the Telegram update."""
    user = update.effective_user
    if user is None:
        return None

    display_name = user.username or user.first_name
    if not display_name:
        return None

    return ChatUser(
        user_id=user.id,
        display_name=display_name,
        username=user.username,
    )


async def zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /zaruba command to create a new event."""
    user = _get_chat_user(update)
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    if not context.args:
        await update.message.reply_text(MESSAGES["zaruba_no_time"])
        return

    time = " ".join(context.args)
    chat_id = update.effective_chat.id

    service = _get_service()
    service.create_zaruba(chat_id, time, user)

    await update.message.reply_text(MESSAGES["zaruba_created"].format(time=time))


async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reg command to register for an event."""
    user = _get_chat_user(update)
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    chat_id = update.effective_chat.id
    custom_time = " ".join(context.args) if context.args else None

    service = _get_service()
    try:
        _, reg_time = service.register_user(chat_id, user, custom_time)
        await update.message.reply_text(
            MESSAGES["reg_success"].format(user=user.display_name, time=reg_time)
        )
    except NoActiveZarubaError:
        await update.message.reply_text(MESSAGES["no_zaruba"])


async def unreg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unreg command to unregister from an event."""
    user = _get_chat_user(update)
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    chat_id = update.effective_chat.id

    service = _get_service()
    if service.unregister_user(chat_id, user):
        await update.message.reply_text(
            MESSAGES["unreg_success"].format(user=user.display_name)
        )
    else:
        await update.message.reply_text(
            MESSAGES["unreg_not_found"].format(user=user.display_name)
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
        members_info = [
            ChatUser(
                user_id=m.user.id,
                display_name=m.user.username or m.user.first_name,
                username=m.user.username,
            )
            for m in members
            if (m.user.username or m.user.first_name) and m.user.username != bot_username
        ]
    except Exception:
        await update.message.reply_text(MESSAGES["list_members_error"])
        return

    if not members_info:
        await update.message.reply_text(MESSAGES["list_members_error"])
        return

    registered_users = session.registered_users
    response_text = f"{MESSAGES['list_registered']}\n"

    for member in members_info:
        if member.display_name in registered_users:
            response_text += MESSAGES["list_reg_yes"].format(
                user=member.display_name, time=registered_users[member.display_name]
            )
        else:
            response_text += MESSAGES["list_reg_no"].format(user=member.display_name)

    await update.message.reply_text(response_text, parse_mode="Markdown")


async def cancel_zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command to cancel an event."""
    user = _get_chat_user(update)
    chat_id = update.effective_chat.id
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    service = _get_service()
    try:
        service.cancel_zaruba(chat_id, user)
        await update.message.reply_text(MESSAGES["cancel_success"])
    except NoActiveZarubaError:
        await update.message.reply_text(MESSAGES["no_zaruba"])


async def botinok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /botinok command to fine a user after two votes."""
    user = _get_chat_user(update)
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    if not context.args:
        await update.message.reply_text(MESSAGES["botinok_no_target"])
        return

    target_username = context.args[0].lstrip("@")
    if not target_username:
        await update.message.reply_text(MESSAGES["botinok_no_target"])
        return
    if target_username == user.display_name:
        await update.message.reply_text(MESSAGES["botinok_self"])
        return

    chat_id = update.effective_chat.id
    service = _get_service()
    try:
        votes, fine_applied, already_voted = service.register_botinok_vote(
            chat_id,
            user.display_name,
            target_username,
        )
    except NoActiveZarubaError:
        await update.message.reply_text(MESSAGES["no_zaruba"])
        return

    if already_voted:
        await update.message.reply_text(
            MESSAGES["botinok_already_voted"].format(
                user=user.display_name,
                target=target_username,
            )
        )
        return

    if fine_applied:
        await update.message.reply_text(
            MESSAGES["botinok_fined"].format(target=target_username)
        )
        return

    await update.message.reply_text(
        MESSAGES["botinok_vote"].format(target=target_username, votes=votes)
    )


async def zaruba_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command to show user statistics."""
    chat_id = update.effective_chat.id
    args = context.args

    try:
        if args:
            username = args[0].lstrip("@")
        else:
            user = _get_chat_user(update)
            if not user:
                await update.message.reply_text(MESSAGES["stats_user_invalid"])
                return
            username = user.display_name
    except Exception:
        await update.message.reply_text(MESSAGES["stats_user_invalid"])
        return

    service = _get_service()
    try:
        if args:
            stats = service.get_user_stats(chat_id, username=username)
            aura = service.get_user_aura(chat_id, username=username)
        else:
            stats = service.get_user_stats(chat_id, user_id=user.user_id, username=username)
            aura = service.get_user_aura(chat_id, user_id=user.user_id, username=username)
    except StatsNotFoundError:
        await update.message.reply_text(MESSAGES["stats_not_found"].format(user=username))
        return

    await update.message.reply_text(
        MESSAGES["list_stats"].format(
            user=stats.person_name,
            aura=aura.aura_points,
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
