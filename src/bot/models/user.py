"""User identity models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatUser:
    """Represents a Telegram user inside a specific chat."""

    user_id: int
    display_name: str
    username: str | None = None
