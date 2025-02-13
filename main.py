import logging
import os
from telegram.ext import ApplicationBuilder
from bot.handlers import get_handlers
from dotenv import load_dotenv
from bot.football_updates import start_scheduler
from bot.db_utils import init_db

load_dotenv()
init_db()

logging.basicConfig(level=logging.INFO)
application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

if __name__ == '__main__':
   

    for handler in get_handlers():
        application.add_handler(handler)

    start_scheduler(application)

    application.run_polling()
