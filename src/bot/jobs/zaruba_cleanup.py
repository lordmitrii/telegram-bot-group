"""Zaruba cleanup job."""

import datetime
import logging

from telegram.ext import Application, ContextTypes

from src.bot.core.constants import MOSCOW_TZ
from src.bot.models.user import ChatUser
from src.bot.repositories.session import get_session_repo
from src.bot.services.zaruba import ZarubaService


async def auto_cancel_zarubas(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Apply nightly absence penalties and auto-cancel all active zaruba sessions."""
    session_repo = get_session_repo()
    service = ZarubaService(session_repo=session_repo)

    for session in session_repo.get_all_sessions():
        try:
            bot_username = context.bot.username
            members = await context.bot.get_chat_administrators(session.chat_id)
            members_info = [
                ChatUser(
                    user_id=member.user.id,
                    display_name=member.user.username or member.user.first_name,
                    username=member.user.username,
                )
                for member in members
                if (member.user.username or member.user.first_name)
                and member.user.username != bot_username
            ]
        except Exception:
            logging.exception(
                "Failed to fetch members before nightly cleanup for chat %s",
                session.chat_id,
            )
            members_info = []

        penalized = service.apply_absence_penalties(session.chat_id, members_info)
        if penalized:
            logging.info(
                "Applied nightly zaruba absence penalties in chat %s: %s",
                session.chat_id,
                penalized,
            )

    deleted = session_repo.delete_all_sessions()
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
