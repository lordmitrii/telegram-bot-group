"""Zaruba-related models."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class ZarubaSession:
    """Represents an active zaruba session for a chat."""

    chat_id: int
    zaruba_time: str
    registered_users: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class ZarubaStats:
    """User statistics for zaruba participation."""

    person_name: str
    chat_id: int
    zarub_initiated: int = 0
    zarub_reg: int = 0
    zarub_canceled: int = 0
    zarub_unreg: int = 0

    @property
    def reliability_score(self) -> float:
        """Calculate the reliability score (lower is better).

        Returns the ratio of negative actions (cancel + unreg) to positive ones (initiate + reg).
        """
        positive = self.zarub_initiated + self.zarub_reg
        negative = self.zarub_canceled + self.zarub_unreg
        if positive == 0:
            return 0.0
        return negative / positive
