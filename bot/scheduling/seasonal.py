import datetime
import logging

from telegram.ext import Application, ContextTypes

from bot.config import UTC_TZ
from bot.db.repositories import get_subscribers


async def send_new_year_message(context: ContextTypes.DEFAULT_TYPE):
    """One-off New Year greeting."""
    application = context.job.data
    subscribers = get_subscribers()

    if not subscribers:
        logging.info("No subscribers for New Year greeting.")
        return

    for chat_id in subscribers:
        try:
            await application.bot.send_message(chat_id=chat_id, text="С новыми годом братва")
        except Exception as exc:
            logging.error("Error sending New Year greeting to %s: %s", chat_id, exc)


def schedule_new_year_message(application: Application):
    """Schedule a single New Year greeting at 21:00 GMT on December 31."""
    now = datetime.datetime.now(UTC_TZ)
    target_time = UTC_TZ.localize(datetime.datetime(now.year, 12, 31, 21, 0))

    if now >= target_time:
        target_time = UTC_TZ.localize(datetime.datetime(now.year + 1, 12, 31, 21, 0))

    if application.job_queue.get_jobs_by_name("new_year_greeting"):
        return

    application.job_queue.run_once(
        send_new_year_message,
        target_time,
        name="new_year_greeting",
        data=application,
    )
