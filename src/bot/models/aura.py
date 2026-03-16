"""Aura-related models."""

from dataclasses import dataclass


@dataclass
class UserAura:
    """Tracks aura points for a user within a chat."""

    person_name: str
    chat_id: int
    aura_points: int = 0
    user_id: int | None = None
