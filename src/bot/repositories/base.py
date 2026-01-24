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

    # Zaruba sessions table (per-chat state)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zaruba_sessions (
            chat_id INTEGER PRIMARY KEY,
            zaruba_time TEXT,
            registered_users TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
