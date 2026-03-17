"""Zaruba command handlers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.core.exceptions import NoActiveZarubaError, StatsNotFoundError
from src.bot.i18n.messages import MESSAGES
from src.bot.models.user import ChatUser
from src.bot.services.zaruba import ZarubaService

# Service instance (will be initialized on first use)
_zaruba_service = None
_BOTINOK_CALLBACK_PREFIX = "botinok:"
_ZARUBA_CALLBACK_PREFIX = "zaruba:"


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


def _get_botinok_markup(target_username: str) -> InlineKeyboardMarkup:
    """Build inline voting markup for a botinok target."""
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                MESSAGES["botinok_button"].format(target=target_username),
                callback_data=f"{_BOTINOK_CALLBACK_PREFIX}{target_username}",
            )
        ]]
    )


def _get_zaruba_markup() -> InlineKeyboardMarkup:
    """Build inline action buttons for the active zaruba message."""
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                MESSAGES["zaruba_button_reg"],
                callback_data=f"{_ZARUBA_CALLBACK_PREFIX}reg",
            ),
            InlineKeyboardButton(
                MESSAGES["zaruba_button_unreg"],
                callback_data=f"{_ZARUBA_CALLBACK_PREFIX}unreg",
            ),
            InlineKeyboardButton(
                MESSAGES["zaruba_button_cancel"],
                callback_data=f"{_ZARUBA_CALLBACK_PREFIX}cancel",
            ),
        ]]
    )


def _is_zaruba_creator(session, user: ChatUser) -> bool:
    """Check whether the user created the current zaruba."""
    if not session.registered_users:
        return False
    creator_username = next(iter(session.registered_users))
    return creator_username == user.display_name


def _format_zaruba_message(session) -> str:
    """Render the zaruba message with the current registered users."""
    response_text = (
        f"{MESSAGES['zaruba_created'].format(time=session.zaruba_time)}\n\n"
        f"{MESSAGES['list_registered']}\n"
    )
    for username, reg_time in session.registered_users.items():
        response_text += MESSAGES["list_reg_yes"].format(user=username, time=reg_time)
    return response_text


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
    session = service.create_zaruba(chat_id, time, user)

    await update.message.reply_text(
        _format_zaruba_message(session),
        reply_markup=_get_zaruba_markup(),
        parse_mode="Markdown",
    )


async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reg command to register for an event."""
    user = _get_chat_user(update)
    if not user:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return

    chat_id = update.effective_chat.id
    custom_time = " ".join(context.args) if context.args else None

    service = _get_service()
    session = service.get_session(chat_id)
    if session is not None and user.display_name in session.registered_users:
        await update.message.reply_text(
            MESSAGES["reg_already_registered"].format(user=user.display_name)
        )
        return
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
    session = service.get_session(chat_id)
    if session is not None and _is_zaruba_creator(session, user):
        await update.message.reply_text(
            MESSAGES["unreg_creator_forbidden"].format(user=user.display_name)
        )
        return
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
    session = service.get_session(chat_id)
    if session is None:
        await update.message.reply_text(MESSAGES["no_zaruba"])
        return
    if not _is_zaruba_creator(session, user):
        await update.message.reply_text(MESSAGES["zaruba_action_only_creator_cancel"])
        return
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
    votes, fine_applied, already_voted = service.register_botinok_vote(
        chat_id,
        user.display_name,
        target_username,
    )

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
        MESSAGES["botinok_vote"].format(target=target_username, votes=votes),
        reply_markup=_get_botinok_markup(target_username),
    )


async def botinok_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline botinok votes."""
    query = update.callback_query
    if query is None or not query.data.startswith(_BOTINOK_CALLBACK_PREFIX):
        return

    user = _get_chat_user(update)
    if not user:
        await query.answer(MESSAGES["zaruba_no_username"], show_alert=True)
        return

    target_username = query.data.removeprefix(_BOTINOK_CALLBACK_PREFIX)
    if not target_username:
        await query.answer(MESSAGES["botinok_no_target"], show_alert=True)
        return
    if target_username == user.display_name:
        await query.answer(MESSAGES["botinok_self"], show_alert=True)
        return

    chat_id = update.effective_chat.id
    service = _get_service()
    votes, fine_applied, already_voted = service.register_botinok_vote(
        chat_id,
        user.display_name,
        target_username,
    )

    if already_voted:
        await query.answer(
            MESSAGES["botinok_already_voted"].format(
                user=user.display_name,
                target=target_username,
            ),
            show_alert=True,
        )
        return

    await query.answer()

    if fine_applied:
        await query.edit_message_text(MESSAGES["botinok_fined"].format(target=target_username))
        return

    await query.edit_message_text(
        MESSAGES["botinok_vote"].format(target=target_username, votes=votes),
        reply_markup=_get_botinok_markup(target_username),
    )


async def zaruba_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline zaruba action buttons."""
    query = update.callback_query
    if query is None or not query.data.startswith(_ZARUBA_CALLBACK_PREFIX):
        return

    user = _get_chat_user(update)
    if not user:
        await query.answer(MESSAGES["zaruba_no_username"], show_alert=True)
        return

    action = query.data.removeprefix(_ZARUBA_CALLBACK_PREFIX)
    chat_id = update.effective_chat.id
    service = _get_service()
    session = service.get_session(chat_id)

    if session is None:
        await query.answer(MESSAGES["no_zaruba"], show_alert=True)
        return

    is_registered = user.display_name in session.registered_users
    is_creator = _is_zaruba_creator(session, user)

    if action == "reg":
        if is_registered:
            await query.answer(
                MESSAGES["zaruba_action_only_unregistered_reg"],
                show_alert=True,
            )
            return
        try:
            _, reg_time = service.register_user(chat_id, user)
        except NoActiveZarubaError:
            await query.answer(MESSAGES["no_zaruba"], show_alert=True)
            return

        await query.answer()
        await query.edit_message_text(
            _format_zaruba_message(service.get_session(chat_id)),
            reply_markup=_get_zaruba_markup(),
            parse_mode="Markdown",
        )
        return

    if action == "unreg":
        if not is_registered:
            await query.answer(
                MESSAGES["zaruba_action_only_registered_unreg"],
                show_alert=True,
            )
            return
        if is_creator:
            await query.answer(
                MESSAGES["unreg_creator_forbidden"].format(user=user.display_name),
                show_alert=True,
            )
            return
        await query.answer()
        if service.unregister_user(chat_id, user):
            await query.edit_message_text(
                _format_zaruba_message(service.get_session(chat_id)),
                reply_markup=_get_zaruba_markup(),
                parse_mode="Markdown",
            )
        else:
            await query.answer(
                MESSAGES["unreg_not_found"].format(user=user.display_name),
                show_alert=True,
            )
        return

    if action == "cancel":
        if not is_creator:
            await query.answer(
                MESSAGES["zaruba_action_only_creator_cancel"],
                show_alert=True,
            )
            return
        try:
            service.cancel_zaruba(chat_id, user)
        except NoActiveZarubaError:
            await query.answer(MESSAGES["no_zaruba"], show_alert=True)
            return

        await query.answer()
        await query.edit_message_text(MESSAGES["cancel_success"])
        return

    await query.answer()


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
    reliability_label = (
        MESSAGES["stats_good_label"] if is_reliable else MESSAGES["stats_bad_label"]
    )
    aura_label = service.get_aura_verdict_label(chat_id, aura.aura_points)

    await update.message.reply_text(
        MESSAGES["stats_verdict_combined"].format(
            reliability=reliability_label,
            aura=aura_label,
            chance=chance,
        ),
        parse_mode="Markdown",
    )
