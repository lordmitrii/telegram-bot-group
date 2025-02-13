import requests
import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot.db_utils import add_subscriber, remove_subscriber, get_subscribers
from bot.messages import MESSAGES 



LEAGUES = {
    "Premier League": ["Liverpool", "Arsenal", "Manchester United", "Manchester City", "Chelsea", "Tottenham"],
    "La Liga": ["Barcelona", "Atletico Madrid", "Real Madrid"],
    "Bundesliga": ["Bayern Munich", "Borussia Dortmund", "Bayer Leverkusen"],
    "Serie A": ["AC Milan", "Inter Milan", "Atalanta"],
    "Premier League": ["Celtic", "Rangers"],
    "UEFA Champions League": "all"  # Include all UCL matches
}

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
    """Filters today's matches based on top leagues and teams"""
    fixtures = await fetch_fixtures()
    big_games = []

    for match in fixtures:
        league = match["competition"]["name"]
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        match_time = match["utcDate"]

        if league == "UEFA Champions League":
            big_games.append((league, home_team, away_team, match_time))

        elif league in LEAGUES and home_team in LEAGUES[league] and away_team in LEAGUES[league]:
            big_games.append((league, home_team, away_team, match_time))

    return big_games

async def send_match_notifications(application):
    """Sends today's big match notifications to the chat"""
    big_games = await get_big_matches()

    subscribers = get_subscribers()
    
    if big_games:
        
        if not subscribers:
            logging.info("No subscribers found.")
            return
        
        message = "🔥 *Сегодняшний футбольчик:*\n\n"
        for league, home, away, time in big_games:
            match_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M UTC")
            message += f"⚽ *{home} vs {away}* ({league})\n⏰ *{match_time}*\n\n"
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


scheduler = BackgroundScheduler(timezone="UTC")

def start_scheduler(application):
    """Starts the scheduler"""
    scheduler.add_job(lambda: asyncio.run(send_match_notifications(application)), "cron", hour=8, minute=0)
    scheduler.start()