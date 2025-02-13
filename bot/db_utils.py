import sqlite3
import os
import json

with open("config.json", "r") as config_file:
    config = json.load(config_file)

DB_PATH = config.get("DB_PATH", "db.slite3")


def init_db():
    """Creates the database and table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def add_subscriber(chat_id):
    """Adds a chat ID to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def remove_subscriber(chat_id):
    """Removes a chat ID from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def get_subscribers():
    """Fetches all subscribed chat IDs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chat_ids