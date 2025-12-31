import requests
import os
import json
import logging
import pytz
import datetime
from telegram.ext import Application
from telegram import Update
from telegram.ext import ContextTypes
from bot.db_utils import add_subscriber, remove_subscriber, get_subscribers
from bot.messages import MESSAGES 


with open("team_ids.json", "r", encoding="utf-8") as file:
    TEAMS = json.load(file)

TEAMS_DICT = {team["team_id"]: {"team_name": team["team_name"], "team_league": team["team_league"]} for team in TEAMS}

# Use Football-Data API query for today's matches
URL = "https://api.football-data.org/v4/matches?TODAY"
HEADERS = {"X-Auth-Token": os.getenv("FOOTBALL_API_KEY")}  # Replace with your actual key

CHAT_ID = os.getenv("CHAT_ID")  

async def fetch_fixtures():
    """Fetches today's fixtures from Football-Data.org"""
    response = requests.get(URL, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json().get("matches", [])
    else:
        logging.error(f"❌ Error fetching fixtures: {response.status_code} - {response.text}")
        return []

async def get_big_matches():
    """Filters today's matches based on top leagues and teams with partial matching"""
    fixtures = await fetch_fixtures()
    big_games = []


    for match in fixtures:
        league_id = match["competition"]["id"]
        league_name_api = match["competition"]["name"]
        home_team_api = match["homeTeam"]
        away_team_api = match["awayTeam"]
        match_time_api = match["utcDate"]

        if league_id == 2001 or league_name_api == "UEFA Champions League":
            home_team = home_team_api["name"]
            away_team = away_team_api["name"]

            if home_team_api["id"] in TEAMS_DICT.keys():
                home_team = TEAMS_DICT[home_team_api["id"]]["team_name"]
            if away_team_api["id"] in TEAMS_DICT.keys():
                away_team = TEAMS_DICT[away_team_api["id"]]["team_name"]

            big_games.append((league_name_api, home_team, away_team, match_time_api))

        elif home_team_api["id"] in TEAMS_DICT.keys() and away_team_api["id"] in TEAMS_DICT.keys():
            home_team = TEAMS_DICT[home_team_api["id"]]["team_name"]
            away_team = TEAMS_DICT[away_team_api["id"]]["team_name"]
            if TEAMS_DICT[home_team_api["id"]]["team_league"] == TEAMS_DICT[away_team_api["id"]]["team_league"]:
                league_name = TEAMS_DICT[home_team_api["id"]]["team_league"]
                big_games.append((league_name, home_team, away_team, match_time_api))
            else:
                big_games.append((league_name_api, home_team, away_team, match_time_api))

    return big_games

async def send_match_notifications(context):
    """Fetch today's matches and notify subscribers."""
    application = context.job.data

    big_games = await get_big_matches()  

    if not big_games:
        logging.info("No big games today.")
        return

    subscribers = get_subscribers()  
    if not subscribers:
        logging.info("No subscribers found.")
        return

    message = MESSAGES["todays_football"]
    for league, home, away, time in big_games:
        match_time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z").astimezone(
            pytz.timezone("Europe/Moscow")
        ).strftime("%H:%M MSC")

        message += MESSAGES["football_game"].format(
            home=home, away=away, league=league, match_time=match_time
        )

    for chat_id in subscribers:
        try:
            await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Error sending message to {chat_id}: {e}")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /subscribe command to add chat ID to the database."""
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text(MESSAGES["subscribe"])

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /unsubscribe command to remove chat ID from the database."""
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text(MESSAGES["unsubscribe"])



def schedule_jobs(application: Application):
    """Schedules the daily football notification job."""
    moscow_tz = pytz.timezone("Europe/Moscow")
    job_time = datetime.time(hour=11, minute=0, tzinfo=moscow_tz)

    application.job_queue.run_daily(
        send_match_notifications,
        job_time,
        name="football_updates",
        data=application, 
    )

    schedule_new_year_message(application)


async def send_new_year_message(context):
    """One-off New Year greeting."""
    application = context.job.data
    subscribers = get_subscribers()

    if not subscribers:
        logging.info("No subscribers for New Year greeting.")
        return

    for chat_id in subscribers:
        try:
            await application.bot.send_message(chat_id=chat_id, text="С новыми годом братва")
        except Exception as e:
            logging.error(f"Error sending New Year greeting to {chat_id}: {e}")


def schedule_new_year_message(application: Application):
    """Schedule a single New Year greeting at 21:00 GMT on December 31."""
    tz = pytz.timezone("UTC")
    now = datetime.datetime.now(tz)
    target_time = tz.localize(datetime.datetime(now.year, 12, 31, 21, 0))

    if now >= target_time:
        target_time = tz.localize(datetime.datetime(now.year + 1, 12, 31, 21, 0))

    if application.job_queue.get_jobs_by_name("new_year_greeting"):
        return

    application.job_queue.run_once(
        send_new_year_message,
        target_time,
        name="new_year_greeting",
        data=application,
    )
   
