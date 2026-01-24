"""Application factory for the Telegram bot."""

import logging
from typing import Optional

from telegram.ext import Application, ApplicationBuilder

from src.bot.core.config import Settings, get_settings
from src.bot.handlers import get_handlers
from src.bot.jobs import schedule_all_jobs
from src.bot.repositories.base import init_db


def create_app(settings: Optional[Settings] = None) -> Application:
    """Create and configure the Telegram bot application.

    Args:
        settings: Optional settings instance (uses default if not provided)

    Returns:
        Configured Application instance
    """
    if settings is None:
        settings = get_settings()

    # Initialize database
    init_db(settings.db_path)

    # Build application
    application = ApplicationBuilder().token(settings.token).build()

    # Register handlers
    for handler in get_handlers():
        application.add_handler(handler)

    # Schedule jobs
    schedule_all_jobs(application)

    return application


def run_app(application: Optional[Application] = None) -> None:
    """Run the bot application.

    Args:
        application: Optional pre-configured application
    """
    if application is None:
        application = create_app()

    logging.info("Starting bot...")
    application.run_polling()
