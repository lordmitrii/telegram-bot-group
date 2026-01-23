import logging
import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from bot.db.repositories import init_db
from bot.handlers import get_handlers
from bot.scheduling.scheduler import schedule_jobs

load_dotenv()
init_db()

logging.basicConfig(level=logging.INFO)
application = ApplicationBuilder().token(os.getenv("TOKEN")).build()


if __name__ == '__main__':

    for handler in get_handlers():
        application.add_handler(handler)

    schedule_jobs(application)

    application.run_polling()
