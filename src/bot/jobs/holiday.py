"""Holiday notification job."""

import datetime
from html import escape
import logging

from telegram.ext import Application, ContextTypes

from src.bot.core.constants import MOSCOW_TZ
from src.bot.i18n.messages import MESSAGES
from src.bot.repositories.subscriber import get_subscribers
from src.bot.services.holiday import HolidayService


async def send_holiday_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch today's holiday and notify subscribers."""
    application = context.job.data
    subscribers = get_subscribers()
    if not subscribers:
        logging.info("No subscribers found for holiday notifications.")
        return

    holiday = await HolidayService().get_todays_holiday()
    if holiday is None:
        logging.info("No holiday found for today.")
        return

    message = MESSAGES["todays_holiday"].format(
        title=escape(holiday.title),
        description=escape(
            holiday.description or MESSAGES["holiday_fallback_description"]
        ),
    )

    for chat_id in subscribers:
        try:
            await application.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
            )
        except Exception as exc:
            logging.error(f"Error sending holiday message to {chat_id}: {exc}")



def schedule_holiday_updates(application: Application) -> None:
    """Schedule the holiday notification job."""
    job_time = datetime.time(hour=10, minute=0, tzinfo=MOSCOW_TZ)

    if application.job_queue.get_jobs_by_name("holiday_updates"):
        return

    application.job_queue.run_repeating(
        send_holiday_notifications,
        interval=job_time,
        first=job_time,
        name="holiday_updates",
        data=application,
    )

