import logging
import os
from telegram import Update, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global variables
zaruba_time = None  # Stores the scheduled Zaruba time
registered_users = {}  # Stores {username: time they registered for}

# /zaruba command - Starts a new event and resets the registration list
async def zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global zaruba_time
    global registered_users
    registered_users.clear()  # Clear previous registrations

    user_name = update.effective_user.username or update.effective_user.first_name

    if not user_name:
        await update.message.reply_text("❌ Не удалось определить ваше имя пользователя. Попробуйте снова.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите время зарубы. Команда: /zaruba <время>")
        return
    
    # Store registration time as text
    if context.args:
        reg_time = " ".join(context.args)  # User-specified time
        registered_users[user_name] = reg_time

    zaruba_time = " ".join(context.args)
    response_text = f"🏆 Открывается регистрация на зарубу в {zaruba_time}.\nДля записи, напишите /reg <optional: время>"
    await update.message.reply_text(response_text)

# /reg command - Registers a user with their selected time
async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global zaruba_time
    global registered_users

    user_name = update.effective_user.username or update.effective_user.first_name

    if not user_name:
        await update.message.reply_text("❌ Не удалось определить ваше имя пользователя. Попробуйте снова.")
        return
    
    if zaruba_time is None:
        await update.message.reply_text("❌ Нет активной зарубы. Сначала создайте её командой /zaruba <время>.")
        return

    if context.args:
        reg_time = " ".join(context.args)  # User-specified time
    elif zaruba_time:
        reg_time = zaruba_time  # Default to zaruba_time if no time is specified
    else:
        await update.message.reply_text("❌ Нет активной зарубы. Сначала создайте её командой /zaruba <время>.") 
        return

    # Store registration time as text
    registered_users[user_name] = reg_time

    response_text = f"✅ @{user_name}, вы зарегистрированы на вечернюю зарубу в {reg_time}!"
    await update.message.reply_text(response_text)

# /list command - Shows all users in the group and their registration status
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users
    global zaruba_time

    chat = await context.bot.get_chat(update.effective_chat.id)
    bot_username = context.bot.username  # Get bot's username to exclude it

    members = [member for member in await context.bot.get_chat_administrators(chat.id)]
    member_usernames = [m.user.username or m.user.first_name for m in members if m.user.username != bot_username]  # Exclude bot

    if not member_usernames:
        await update.message.reply_text("❌ Не удалось получить список участников группы.")
        return
    
    if zaruba_time is None:
        response_text = "🚫 Заруба пока не намечается."

    else:
        response_text = "📜 Список участников зарубы:\n"
        for username in member_usernames:
            if username in registered_users:
                reg_time = registered_users[username]
                response_text += f"✅ @{username} зарегистрирован на {reg_time}\n"
            else:
                response_text += f"❌ @{username} не зарегистрирован\n"

    await update.message.reply_text(response_text)

# /cancel command - Cancels an ongoing zaruba
async def cancel_zaruba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global zaruba_time
    global registered_users

    if zaruba_time is None:
        await update.message.reply_text("❌ Нет активной зарубы для отмены.")
        return

    zaruba_time = None
    registered_users.clear()  # Clear all registered users

    await update.message.reply_text("🚫 Заруба отменена. Регистрация закрыта.")

# /unreg command - Allows a user to unregister
async def unreg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users

    user_name = update.effective_user.username or update.effective_user.first_name

    if user_name in registered_users:
        del registered_users[user_name]
        await update.message.reply_text(f"🚫 @{user_name}, вы отменили регистрацию на зарубу.")
    else:
        await update.message.reply_text(f"❌ @{user_name}, вы не были зарегистрированы.")

# /start command - Introduction
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Используйте /zaruba <время> для создания зарубы, /reg для записи, /list для просмотра и /cancel для отмены.")

# /unknown command handler
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Неизвестная команда. Попробуйте /zaruba, /reg, /list или /cancel.")

# Main function
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.environ.get("TOKEN")).build()

    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('zaruba', zaruba))
    application.add_handler(CommandHandler('reg', reg))
    application.add_handler(CommandHandler('unreg', unreg))
    application.add_handler(CommandHandler('list', list_users))
    application.add_handler(CommandHandler('cancel', cancel_zaruba))
    application.add_handler(CommandHandler("unknown", unknown))

    # Start polling
    application.run_polling()
