import json
import os

import pytz

# Load config.json
with open("config.json", "r") as config_file:
    _config = json.load(config_file)

# Database path
_db_path = _config.get("DB_PATH", "db.sqlite3")


def get_db_path():
    return _db_path


def set_db_path(path):
    global _db_path
    _db_path = path


# Constants
BAD_THRESHOLD = 0.2

# Timezones
MOSCOW_TZ = pytz.timezone("Europe/Moscow")
UTC_TZ = pytz.timezone("UTC")

# Football API
FOOTBALL_API_URL = "https://api.football-data.org/v4/matches?TODAY"
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

# Scraper
try:
    SCRAPER_POLL_INTERVAL_SECONDS = int(os.getenv("SCRAPER_POLL_INTERVAL", "300"))
except ValueError:
    SCRAPER_POLL_INTERVAL_SECONDS = 300
