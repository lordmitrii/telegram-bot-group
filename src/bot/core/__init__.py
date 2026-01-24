"""Core module containing configuration, constants, and exceptions."""

from src.bot.core.config import Settings, get_settings
from src.bot.core.constants import BAD_THRESHOLD, MOSCOW_TZ, UTC_TZ
from src.bot.core.exceptions import (
    BotError,
    NoActiveZarubaError,
    UserNotFoundError,
    StatsNotFoundError,
)

__all__ = [
    "Settings",
    "get_settings",
    "BAD_THRESHOLD",
    "MOSCOW_TZ",
    "UTC_TZ",
    "BotError",
    "NoActiveZarubaError",
    "UserNotFoundError",
    "StatsNotFoundError",
]
