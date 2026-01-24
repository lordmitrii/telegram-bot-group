"""Subscriber model."""

from dataclasses import dataclass


@dataclass
class Subscriber:
    """Represents a chat subscribed to notifications."""

    chat_id: int
