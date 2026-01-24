"""Custom exceptions for the bot application."""


class BotError(Exception):
    """Base exception for bot errors."""

    pass


class NoActiveZarubaError(BotError):
    """Raised when an operation requires an active zaruba but none exists."""

    pass


class UserNotFoundError(BotError):
    """Raised when a user is not found in the context."""

    pass


class StatsNotFoundError(BotError):
    """Raised when user statistics are not found."""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"No stats found for user @{username}")
