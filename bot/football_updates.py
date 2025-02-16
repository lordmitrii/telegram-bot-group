import requests
import os
import json
import logging
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
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

async def send_match_notifications(application):
    """Sends today's big match notifications to the chat"""
    big_games = await get_big_matches()

    subscribers = get_subscribers()
    
    if big_games:
        
        if not subscribers:
            logging.info("No subscribers found.")
            return

        message = MESSAGES["todays_football"]
        for league, home, away, time in big_games:
            match_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.timezone("Europe/Moscow")).strftime("%H:%M MSC")
            message += MESSAGES["football_game"].format(home=home, away=away, league=league, match_time=match_time)
        for chat_id in subscribers:
            try:
                await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Error sending message to {chat_id}: {e}")
    else:
        pass


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


scheduler = BackgroundScheduler(timezone="Europe/Moscow")

def start_scheduler(application):
    """Starts the scheduler"""
    scheduler.add_job(lambda: asyncio.run(send_match_notifications(application)), "interval", minutes=1)
    scheduler.start()