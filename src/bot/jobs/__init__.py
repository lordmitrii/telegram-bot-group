"""Job scheduling module."""

import logging

from telegram.ext import Application

from src.bot.jobs.football import schedule_football_updates
from src.bot.jobs.holiday import schedule_holiday_updates
from src.bot.jobs.scraper import schedule_scraper_polling
from src.bot.jobs.seasonal import schedule_new_year_message
from src.bot.jobs.zaruba_cleanup import schedule_zaruba_cleanup


def schedule_all_jobs(application: Application) -> None:
    """Schedule all recurring jobs."""
    schedule_football_updates(application)
    schedule_holiday_updates(application)
    # schedule_scraper_polling(application)
    schedule_new_year_message(application)
    schedule_zaruba_cleanup(application)
    logging.info(
        "Scheduled jobs: football updates, holiday updates, scrapers, seasonal messages, cleanup."
    )


__all__ = [
    "schedule_all_jobs",
    "schedule_football_updates",
    "schedule_holiday_updates",
    "schedule_scraper_polling",
    "schedule_new_year_message",
    "schedule_zaruba_cleanup",
]
