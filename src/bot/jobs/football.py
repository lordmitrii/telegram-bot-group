"""Football notification job."""

import datetime
import logging

from telegram.ext import Application, ContextTypes

from src.bot.core.constants import MOSCOW_TZ
from src.bot.i18n.messages import MESSAGES
from src.bot.repositories.subscriber import get_subscribers
from src.bot.services.football import FootballService
from src.bot.services.zaruba import ZarubaService


async def send_match_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch today's matches and notify subscribers."""
    application = context.job.data

    service = FootballService()
    big_games = await service.get_big_matches()

    if not big_games:
        logging.info("No big games today. Sending a placeholder match.")
        return
        

    subscribers = get_subscribers()
    if not subscribers:
        logging.info("No subscribers found.")
        return

    message = MESSAGES["todays_football"]
    for match in big_games:
        match_time = service.format_match_time(match.utc_date)
        message += MESSAGES["football_game"].format(
            home=match.home_team,
            away=match.away_team,
            league=match.league,
            match_time=match_time,
        )

    if len(big_games) == 1:
        zaruba_time = service.format_match_time(big_games[0].utc_date)
    else:
        match_times = {service.format_match_time(match.utc_date) for match in big_games}
        if len(match_times) == 1:
            zaruba_time = next(iter(match_times))
        else:
            zaruba_time = MESSAGES["football_time"]
    zaruba_service = ZarubaService()

    for chat_id in subscribers:
        if zaruba_service.get_session(chat_id) is None:
            message += MESSAGES["football_zaruba_cta"]
            zaruba_service.create_zaruba(
                chat_id=chat_id,
                time=zaruba_time,
                creator_username="football_bot",
            )
        try:
            await application.bot.send_message(
                chat_id=chat_id, text=message, parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error sending message to {chat_id}: {e}")


def schedule_football_updates(application: Application) -> None:
    """Schedule the daily football notification job."""
    job_time = datetime.time(hour=11, minute=00, tzinfo=MOSCOW_TZ)

    if application.job_queue.get_jobs_by_name("football_updates"):
        return

    application.job_queue.run_daily(
        send_match_notifications,
        job_time,
        name="football_updates",
        data=application,
    )
