"""Zaruba cleanup job."""

import datetime
import logging

from telegram.ext import Application, ContextTypes

from src.bot.core.constants import MOSCOW_TZ
from src.bot.repositories.session import get_session_repo


async def auto_cancel_zarubas(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-cancel all active zaruba sessions."""
    deleted = get_session_repo().delete_all_sessions()
    logging.info("Auto-canceled zaruba sessions: %s", deleted)


def schedule_zaruba_cleanup(application: Application) -> None:
    """Schedule daily zaruba cleanup at 03:00 Moscow time."""
    job_time = datetime.time(hour=3, minute=0, tzinfo=MOSCOW_TZ)

    if application.job_queue.get_jobs_by_name("zaruba_cleanup"):
        return

    application.job_queue.run_daily(
        auto_cancel_zarubas,
        job_time,
        name="zaruba_cleanup",
        data=application,
    )


__all__ = ["schedule_zaruba_cleanup", "auto_cancel_zarubas"]
