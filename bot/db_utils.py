import sqlite3
import os
import json

with open("config.json", "r") as config_file:
    config = json.load(config_file)

DB_PATH = config.get("DB_PATH", "db.slite3")


def init_db(db_path=DB_PATH):
    """Creates the database and table if not exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zarubbl (
            person_name VARCHAR(32),
            chat_id INTEGER,
            zarub_initiated INTEGER DEFAULT 0,
            zarub_reg INTEGER DEFAULT 0,
            zarub_canceled INTEGER DEFAULT 0,
            zarub_unreg INTEGER DEFAULT 0,      
            PRIMARY KEY (person_name, chat_id)               
        )
    """)

    conn.commit()
    conn.close()

def add_subscriber(chat_id, db_path=DB_PATH):
    """Adds a chat ID to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def remove_subscriber(chat_id, db_path=DB_PATH):
    """Removes a chat ID from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def get_subscribers(db_path=DB_PATH):
    """Fetches all subscribed chat IDs."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chat_ids

def change_zarubbl_counter(person_name, chat_id, type, db_path=DB_PATH):
    """Adjusts zarubbl counters for a given person_name."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO zarubbl (person_name, chat_id) VALUES (?, ?)", (person_name, chat_id))

    if type == "initiate":
        column = "zarub_initiated"
    elif type == "reg":
        column = "zarub_reg"
    elif type == "cancel":
        column = "zarub_canceled"
    else:
        column = "zarub_unreg"

    query = f"UPDATE zarubbl SET {column} = {column} + 1 WHERE person_name = ? AND chat_id = ?"
    cursor.execute(query, (person_name, chat_id))

    conn.commit()
    conn.close()

def get_zarubbl_stats(chat_id, person_name, db_path=DB_PATH):
    """Get zarubbl stats for a given person_name."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM zarubbl WHERE chat_id = ? AND person_name = ?", (chat_id, person_name))
    row = cursor.fetchall()[0]
    stats = {"zarub_initiated": row[2], "zarub_reg": row[3], "zarub_canceled": row[4], "zarub_unreg": row[5]}

    conn.close()
    return stats
