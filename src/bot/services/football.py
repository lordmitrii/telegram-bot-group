"""Football service for fetching and filtering matches."""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src.bot.core.config import get_settings
from src.bot.core.constants import MOSCOW_TZ
from src.bot.models.match import Match


class FootballService:
    """Service for football match operations."""

    def __init__(self, teams_file: Optional[Path] = None):
        self._settings = get_settings()
        self._teams_dict = self._load_teams(teams_file)

    def _load_teams(self, teams_file: Optional[Path] = None) -> Dict[int, Dict[str, str]]:
        """Load team ID mappings from JSON file."""
        if teams_file is None:
            teams_file = Path("data/team_ids.json")

        if not teams_file.exists():
            logging.warning(f"Teams file not found: {teams_file}")
            return {}

        with open(teams_file, "r", encoding="utf-8") as f:
            teams = json.load(f)

        return {
            team["team_id"]: {
                "team_name": team["team_name"],
                "team_league": team["team_league"],
            }
            for team in teams
        }

    @property
    def _headers(self) -> Dict[str, str]:
        """Get API headers."""
        return {"X-Auth-Token": self._settings.football_api_key or ""}

    async def fetch_fixtures(self) -> List[dict]:
        """Fetch today's fixtures from Football-Data.org."""
        try:
            response = requests.get(
                self._settings.football_api_url,
                headers=self._headers,
            )
            if response.status_code == 200:
                return response.json().get("matches", [])
            else:
                logging.error(
                    f"Error fetching fixtures: {response.status_code} - {response.text}"
                )
                return []
        except Exception as e:
            logging.error(f"Error fetching fixtures: {e}")
            return []

    async def get_big_matches(self) -> List[Match]:
        """Get important matches for today."""
        fixtures = await self.fetch_fixtures()
        big_games: List[Match] = []

        for match in fixtures:
            league_id = match["competition"]["id"]
            league_name_api = match["competition"]["name"]
            home_team_api = match["homeTeam"]
            away_team_api = match["awayTeam"]
            match_time_api = match["utcDate"]

            # Champions League matches
            if league_id == 2001 or league_name_api == "UEFA Champions League":
                home_team = self._get_team_name(home_team_api)
                away_team = self._get_team_name(away_team_api)
                big_games.append(
                    Match.from_api_data(
                        league=league_name_api,
                        home_team=home_team,
                        away_team=away_team,
                        utc_date=match_time_api,
                    )
                )
            # Matches between known teams
            elif (
                home_team_api["id"] in self._teams_dict
                and away_team_api["id"] in self._teams_dict
            ):
                home_team = self._teams_dict[home_team_api["id"]]["team_name"]
                away_team = self._teams_dict[away_team_api["id"]]["team_name"]
                home_league = self._teams_dict[home_team_api["id"]]["team_league"]
                away_league = self._teams_dict[away_team_api["id"]]["team_league"]

                if home_league == away_league:
                    league_name = home_league
                else:
                    league_name = league_name_api

                big_games.append(
                    Match.from_api_data(
                        league=league_name,
                        home_team=home_team,
                        away_team=away_team,
                        utc_date=match_time_api,
                    )
                )

        return big_games

    def _get_team_name(self, team_api: dict) -> str:
        """Get team name, preferring custom mapping."""
        team_id = team_api["id"]
        if team_id in self._teams_dict:
            return self._teams_dict[team_id]["team_name"]
        return team_api["name"]

    def format_match_time(self, utc_date: str) -> str:
        """Format match time to Moscow timezone."""
        match_time = datetime.datetime.strptime(
            utc_date, "%Y-%m-%dT%H:%M:%S%z"
        ).astimezone(MOSCOW_TZ)
        return match_time.strftime("%H:%M MSC")


# Module-level functions for backwards compatibility
_service: Optional[FootballService] = None


def _get_service() -> FootballService:
    global _service
    if _service is None:
        _service = FootballService()
    return _service


async def fetch_fixtures() -> List[dict]:
    """Fetch today's fixtures."""
    return await _get_service().fetch_fixtures()


async def get_big_matches() -> List[tuple]:
    """Get big matches as tuples for backwards compatibility."""
    matches = await _get_service().get_big_matches()
    return [
        (m.league, m.home_team, m.away_team, m.utc_date)
        for m in matches
    ]
