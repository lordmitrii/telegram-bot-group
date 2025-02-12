import logging
import os
from telegram.ext import ApplicationBuilder
from bot.handlers import get_handlers
from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Initialize Bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    # Add Handlers
    for handler in get_handlers():
        application.add_handler(handler)

    # Start Polling
    application.run_polling()
