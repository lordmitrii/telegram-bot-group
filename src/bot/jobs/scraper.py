"""Scraper polling job."""

import logging

from telegram.ext import Application, ContextTypes

from src.bot.core.config import get_settings
from src.bot.repositories.subscriber import get_subscribers
from src.bot.services.scraper import ScraperService

# Shared service instance
_scraper_service = None


def _get_service() -> ScraperService:
    """Get or create the scraper service instance."""
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = ScraperService()
    return _scraper_service


async def poll_scrapers(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll configured scrapers and notify subscribers when available."""
    application = context.job.data

    subscribers = get_subscribers()
    if not subscribers:
        logging.info("No subscribers for scraper notifications.")
        return

    service = _get_service()
    notifications = service.check_availability()

    for name, quantity, url in notifications:
        message = f"🔔 {name}: {quantity} items available! {url}"
        for chat_id in subscribers:
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    disable_web_page_preview=True,
                )
            except Exception as exc:
                logging.error("Error sending scraper update to %s: %s", chat_id, exc)


def schedule_scraper_polling(application: Application) -> None:
    """Schedule scraper polling job."""
    if application.job_queue.get_jobs_by_name("scraper_polling"):
        return

    settings = get_settings()
    interval = max(60, settings.scraper_poll_interval)

    application.job_queue.run_repeating(
        poll_scrapers,
        interval=interval,
        first=5,
        name="scraper_polling",
        data=application,
    )
