"""Football match model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Match:
    """Represents a football match."""

    league: str
    home_team: str
    away_team: str
    utc_date: str
    match_time: Optional[datetime] = None

    @classmethod
    def from_api_data(
        cls,
        league: str,
        home_team: str,
        away_team: str,
        utc_date: str,
    ) -> "Match":
        """Create a Match from API data."""
        return cls(
            league=league,
            home_team=home_team,
            away_team=away_team,
            utc_date=utc_date,
        )
