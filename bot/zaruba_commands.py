import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.messages import MESSAGES 
from bot.db_utils import change_zarubbl_counter, get_zarubbl_stats

# Global state
zaruba_time = None
registered_users = {}
BAD_THRESHOLD = 0.2

async def zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new event and resets the registration list."""
    global zaruba_time, registered_users
    registered_users.clear()
    
    user_name = update.effective_user.username or update.effective_user.first_name
    if not user_name:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return
    
    if not context.args:
        await update.message.reply_text(MESSAGES["zaruba_no_time"])
        return
    
    zaruba_time = " ".join(context.args)
    registered_users[user_name] = zaruba_time
    await update.message.reply_text(MESSAGES["zaruba_created"].format(time=zaruba_time))

    chat_id = update.effective_chat.id
    person_name = update.effective_user.username
    change_zarubbl_counter(person_name=person_name, chat_id=chat_id, type="initiate")

async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registers a user for the event."""
    global registered_users, zaruba_time
    user_name = update.effective_user.username or update.effective_user.first_name

    if not user_name:
        await update.message.reply_text(MESSAGES["zaruba_no_username"])
        return
    
    if zaruba_time is None:
        await update.message.reply_text(MESSAGES["no_zaruba"])
        return

    reg_time = " ".join(context.args) if context.args else zaruba_time
    registered_users[user_name] = reg_time

    await update.message.reply_text(MESSAGES["reg_success"].format(user=user_name, time=reg_time))

    chat_id = update.effective_chat.id
    person_name = update.effective_user.username
    change_zarubbl_counter(person_name=person_name, chat_id=chat_id, type="reg",)

async def unreg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows a user to unregister."""
    global registered_users

    user_name = update.effective_user.username or update.effective_user.first_name

    if user_name in registered_users:
        del registered_users[user_name]
        
        await update.message.reply_text(MESSAGES["unreg_success"].format(user=user_name))

        chat_id = update.effective_chat.id
        person_name = update.effective_user.username
        change_zarubbl_counter(person_name=person_name, chat_id=chat_id, type="unreg")
    else:
        await update.message.reply_text(MESSAGES["unreg_not_found"].format(user=user_name))

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists registered users."""
    global registered_users, zaruba_time


    chat = await context.bot.get_chat(update.effective_chat.id)
    bot_username = context.bot.username 
    members = [member for member in await context.bot.get_chat_administrators(chat.id)]
    member_usernames = [m.user.username or m.user.first_name for m in members if m.user.username != bot_username] 

    if not member_usernames:
        await update.message.reply_text(MESSAGES["list_members_error"])
        return

    if zaruba_time is None:
        await update.message.reply_text(MESSAGES["list_no_zaruba"])
        return

    response_text = f"{MESSAGES['list_registered']}\n"

    for username in member_usernames:
        if username in registered_users:
            response_text += MESSAGES["list_reg_yes"].format(user=username, time=registered_users[username])
        else:
            response_text += MESSAGES["list_reg_no"].format(user=username)

    await update.message.reply_text(response_text, parse_mode="Markdown")

async def cancel_zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels an ongoing zaruba event."""
    global zaruba_time, registered_users

    if zaruba_time is None:
        await update.message.reply_text(MESSAGES["no_zaruba"])
        return
    
    zaruba_time, registered_users = None, {}
    await update.message.reply_text(MESSAGES["cancel_success"])

    chat_id = update.effective_chat.id
    person_name = update.effective_user.username
    change_zarubbl_counter(person_name=person_name, chat_id=chat_id, type="cancel")


async def zaruba_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get zaruba stats on the chat."""
    chat_id = update.effective_chat.id

    args = context.args

    try:
        username = update.effective_user.username if not args else args[0].lstrip("@")
    except:
        await update.message.reply_text("Пользователь указан неправильно. Используйте формат /stats <@пользователь>")
        return


    try:
        stats = get_zarubbl_stats(chat_id=chat_id, person_name=username)
    except IndexError:
        await update.message.reply_text(f"Нет статистики о пользователе @{username}")
        return
    
    await update.message.reply_text(MESSAGES["list_stats"].format(
        user=username, initiated=stats["zarub_initiated"], canceled=stats["zarub_canceled"],
        regnuto=stats["zarub_reg"], unregnuto=stats["zarub_unreg"]
    ), parse_mode="Markdown")

    chance = round((stats["zarub_canceled"] + stats["zarub_unreg"]) \
                        / (stats["zarub_initiated"] + stats["zarub_reg"]), 2)
        

    if chance < BAD_THRESHOLD:

        await update.message.reply_text(MESSAGES["stats_good"].format(chance=chance*100), parse_mode="Markdown")


    else:
        await update.message.reply_text(MESSAGES["stats_bad"].format(chance=chance*100), parse_mode="Markdown")


