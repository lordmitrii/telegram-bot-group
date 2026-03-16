"""Base repository with connection management."""

import sqlite3
from contextlib import contextmanager
from typing import Optional, Generator

from src.bot.core.config import get_db_path


class BaseRepository:
    """Base repository class with database connection management."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path or get_db_path()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database schema."""
    db_path = db_path or get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Subscribers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY
        )
    """)

    # Zaruba stats table
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zarubbl_by_id (
            user_id INTEGER,
            chat_id INTEGER,
            display_name TEXT,
            zarub_initiated INTEGER DEFAULT 0,
            zarub_reg INTEGER DEFAULT 0,
            zarub_canceled INTEGER DEFAULT 0,
            zarub_unreg INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )
    """)

    # Zaruba sessions table (per-chat state)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zaruba_sessions (
            chat_id INTEGER PRIMARY KEY,
            zaruba_time TEXT,
            registered_users TEXT,
            botinok_votes TEXT DEFAULT '{}',
            fined_users TEXT DEFAULT '[]',
            absence_penalties TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_aura (
            person_name VARCHAR(32),
            chat_id INTEGER,
            aura_points INTEGER DEFAULT 0,
            PRIMARY KEY (person_name, chat_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_aura_by_id (
            user_id INTEGER,
            chat_id INTEGER,
            display_name TEXT,
            aura_points INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_identities (
            chat_id INTEGER,
            user_id INTEGER,
            username VARCHAR(32),
            display_name TEXT NOT NULL,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_identities_chat_username
        ON user_identities (chat_id, username)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS botinok_votes (
            chat_id INTEGER,
            target_username TEXT,
            voter_username TEXT,
            PRIMARY KEY (chat_id, target_username, voter_username)
        )
    """)

    cursor.execute("PRAGMA table_info(zaruba_sessions)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "botinok_votes": "ALTER TABLE zaruba_sessions ADD COLUMN botinok_votes TEXT DEFAULT '{}'",
        "fined_users": "ALTER TABLE zaruba_sessions ADD COLUMN fined_users TEXT DEFAULT '[]'",
        "absence_penalties": "ALTER TABLE zaruba_sessions ADD COLUMN absence_penalties TEXT DEFAULT '[]'",
    }
    for column, statement in required_columns.items():
        if column not in existing_columns:
            cursor.execute(statement)

    conn.commit()
    conn.close()
