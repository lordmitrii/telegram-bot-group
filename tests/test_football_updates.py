"""Tests for football service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import pytz

from src.bot.services.football import FootballService, fetch_fixtures, get_big_matches
from src.bot.jobs.football import send_match_notifications
from src.bot.i18n.messages import MESSAGES


@pytest.mark.asyncio
@patch("src.bot.services.football.requests.get")
async def test_fetch_fixtures_success(mock_get):
    """Test fetching fixtures when API returns a valid response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "matches": [
            {
                "competition": {"id": 2001, "name": "UEFA Champions League"},
                "homeTeam": {"id": 64, "name": "Liverpool"},
                "awayTeam": {"id": 65, "name": "Manchester City"},
                "utcDate": "2025-02-14T20:00:00Z",
            }
        ]
    }
    mock_get.return_value = mock_response

    fixtures = await fetch_fixtures()
    assert fixtures == mock_response.json.return_value["matches"]


@pytest.mark.asyncio
@patch("src.bot.services.football.requests.get")
async def test_fetch_fixtures_failure(mock_get):
    """Test fetching fixtures when API returns an error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    fixtures = await fetch_fixtures()
    assert fixtures == []


@pytest.mark.asyncio
@patch("src.bot.services.football.FootballService.fetch_fixtures")
async def test_get_big_matches(mock_fetch_fixtures):
    """Test filtering of important matches."""
    mock_fetch_fixtures.return_value = [
        {
            "competition": {"id": 2001, "name": "UEFA Champions League"},
            "homeTeam": {"id": 64, "name": "Liverpool"},
            "awayTeam": {"id": 65, "name": "Manchester City"},
            "utcDate": "2025-02-14T20:00:00Z",
        },
        {
            "competition": {"id": 2022, "name": "Unknown League"},
            "homeTeam": {"id": 9000, "name": "Random FC"},
            "awayTeam": {"id": 9001, "name": "Unknown United"},
            "utcDate": "2025-02-14T21:00:00Z",
        },
        {
            "competition": {"id": 2013, "name": "Premier League"},
            "homeTeam": {"id": 66, "name": "Manchester United"},
            "awayTeam": {"id": 61, "name": "Chelsea"},
            "utcDate": "2025-02-14T19:00:00Z",
        },
    ]

    # Using module-level function for backwards compatibility
    matches = await get_big_matches()

    # Should include Champions League and Premier League match between known teams
    assert len(matches) == 2
    assert matches[0][0] == "UEFA Champions League"
    assert matches[1][0] == "Premier League"


@pytest.mark.asyncio
@patch("src.bot.jobs.football.ZarubaService")
@patch("src.bot.jobs.football.FootballService")
@patch("src.bot.jobs.football.get_subscribers")
async def test_send_match_notifications(
    mock_get_subscribers, mock_service_class, mock_zaruba_service_class
):
    """Test sending notifications to subscribers."""
    # Setup mock service
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_zaruba_service = MagicMock()
    mock_zaruba_service.get_session.return_value = None
    mock_zaruba_service_class.return_value = mock_zaruba_service

    # Create mock match objects
    from src.bot.models.match import Match
    mock_matches = [
        Match(
            league="Premier League",
            home_team="Manchester United",
            away_team="Chelsea",
            utc_date="2025-02-14T19:00:00Z",
        )
    ]

    async def async_get_big_matches():
        return mock_matches

    mock_service.get_big_matches = async_get_big_matches
    mock_service.format_match_time.return_value = "22:00 MSC"

    mock_get_subscribers.return_value = [123456789, 987654321]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_match_notifications(fake_context)

    assert bot_mock.send_message.call_count == 2
    assert mock_zaruba_service.create_zaruba.call_count == 2


@pytest.mark.asyncio
@patch("src.bot.jobs.football.ZarubaService")
@patch("src.bot.jobs.football.FootballService")
@patch("src.bot.jobs.football.get_subscribers")
async def test_send_match_notifications_same_time_sets_zaruba_time(
    mock_get_subscribers, mock_service_class, mock_zaruba_service_class
):
    """Test that a shared match time is used for zaruba registration."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.format_match_time.return_value = "20:00 MSC"

    async def async_get_big_matches():
        from src.bot.models.match import Match
        return [
            Match(
                league="Premier League",
                home_team="Team A",
                away_team="Team B",
                utc_date="2025-02-14T19:00:00Z",
            ),
            Match(
                league="Premier League",
                home_team="Team C",
                away_team="Team D",
                utc_date="2025-02-14T19:00:00Z",
            ),
        ]

    mock_service.get_big_matches = async_get_big_matches

    mock_get_subscribers.return_value = [123456789]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    mock_zaruba_service = MagicMock()
    mock_zaruba_service.get_session.return_value = None
    mock_zaruba_service_class.return_value = mock_zaruba_service

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_match_notifications(fake_context)

    mock_zaruba_service.create_zaruba.assert_called_once()
    _, kwargs = mock_zaruba_service.create_zaruba.call_args
    assert kwargs["time"] == "20:00 MSC"

@pytest.mark.asyncio
@patch("src.bot.jobs.football.ZarubaService")
@patch("src.bot.jobs.football.FootballService")
@patch("src.bot.jobs.football.get_subscribers")
async def test_send_match_notifications_no_subscribers(
    mock_get_subscribers, mock_service_class, mock_zaruba_service_class
):
    """Test that no notifications are sent if there are no subscribers."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_zaruba_service_class.return_value = MagicMock()

    async def async_get_big_matches():
        return []

    mock_service.get_big_matches = async_get_big_matches
    mock_get_subscribers.return_value = []

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_match_notifications(fake_context)

    bot_mock.send_message.assert_not_called()


@pytest.mark.asyncio
@patch("src.bot.jobs.football.FootballService")
@patch("src.bot.jobs.football.get_subscribers")
async def test_send_match_notifications_no_matches(mock_get_subscribers, mock_service_class):
    """Test that no notifications are sent if there are no big matches."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service

    async def async_get_big_matches():
        return []

    mock_service.get_big_matches = async_get_big_matches
    mock_get_subscribers.return_value = [123456789]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_match_notifications(fake_context)

    bot_mock.send_message.assert_not_called()
