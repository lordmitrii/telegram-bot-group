import logging

from telegram.ext import Application

from bot.services.football import schedule_football_updates
from bot.services.scraper import schedule_scraper_polling
from bot.scheduling.seasonal import schedule_new_year_message


def schedule_jobs(application: Application):
    """Central place to wire up recurring jobs."""
    schedule_football_updates(application)
    schedule_scraper_polling(application)
    schedule_new_year_message(application)
    logging.info("Scheduled jobs: football updates, scrapers, seasonal messages.")
