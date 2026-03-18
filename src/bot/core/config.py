"""Application configuration using Pydantic settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    token: str = Field(..., validation_alias="TOKEN")
    admin_relay_user_id: Optional[int] = Field(
        default=None, validation_alias="ADMIN_RELAY_USER_ID"
    )
    admin_relay_chat_id: Optional[int] = Field(
        default=None, validation_alias="ADMIN_RELAY_CHAT_ID"
    )

    # Database
    db_path: str = Field(default="db.sqlite3", validation_alias="DB_PATH")

    # Football API
    football_api_key: Optional[str] = Field(
        default=None, validation_alias="FOOTBALL_API_KEY"
    )
    football_api_url: str = Field(
        default="https://api.football-data.org/v4/matches?TODAY",
        validation_alias="FOOTBALL_API_URL",
    )

    # Holiday notifications
    holiday_source_url_template: str = Field(
        default="https://www.calend.ru/",
        validation_alias="HOLIDAY_SOURCE_URL_TEMPLATE",
    )

    # Scraper
    scraper_poll_interval: int = Field(
        default=300, validation_alias="SCRAPER_POLL_INTERVAL"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# For backwards compatibility during migration
_db_path: Optional[str] = None


def get_db_path() -> str:
    """Get database path, supporting legacy override."""
    if _db_path is not None:
        return _db_path
    return get_settings().db_path


def set_db_path(path: str) -> None:
    """Set database path (for testing)."""
    global _db_path
    _db_path = path
