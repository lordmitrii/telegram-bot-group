import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.football_updates import fetch_fixtures, get_big_matches, send_match_notifications
from bot.messages import MESSAGES
from datetime import datetime
import pytz


@pytest.mark.asyncio
@patch("bot.football_updates.requests.get")
async def test_fetch_fixtures_success(mock_get):
    """Test fetching fixtures when API returns a valid response"""
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
@patch("bot.football_updates.requests.get")
async def test_fetch_fixtures_failure(mock_get):
    """Test fetching fixtures when API returns an error"""
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    fixtures = await fetch_fixtures()
    assert fixtures == []  


@pytest.mark.asyncio
@patch("bot.football_updates.fetch_fixtures")
async def test_get_big_matches(mock_fetch_fixtures):
    """Test filtering of important matches"""
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

    expected_matches = [
        ("UEFA Champions League", "Liverpool", "Manchester City", "2025-02-14T20:00:00Z"),
        ("Premier League", "Manchester United", "Chelsea", "2025-02-14T19:00:00Z"),
    ]

    matches = await get_big_matches()
    assert matches == expected_matches


@pytest.mark.asyncio
@patch("bot.football_updates.get_big_matches")
@patch("bot.football_updates.get_subscribers")
async def test_send_match_notifications(mock_get_subscribers, mock_get_big_matches):
    """Test sending notifications to subscribers"""
    mock_get_big_matches.return_value = [
        ("Premier League", "Manchester United", "Chelsea", "2025-02-14T19:00:00Z")
    ]
    mock_get_subscribers.return_value = [123456789, 987654321]  # Mocked chat IDs

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    # Dynamically format the message using `MESSAGES`
    match_time = datetime.strptime(
        "2025-02-14T19:00:00Z", "%Y-%m-%dT%H:%M:%SZ"
    ).astimezone(pytz.timezone("Europe/Moscow")).strftime("%H:%M MSC")

    expected_message = MESSAGES["todays_football"]
    expected_message += MESSAGES["football_game"].format(
        home="Manchester United", away="Chelsea", league="Premier League", match_time=match_time
    )

    await send_match_notifications(fake_context)

    bot_mock.send_message.assert_any_call(chat_id=123456789, text=expected_message, parse_mode="Markdown")
    bot_mock.send_message.assert_any_call(chat_id=987654321, text=expected_message, parse_mode="Markdown")

    assert bot_mock.send_message.call_count == 2


@pytest.mark.asyncio
@patch("bot.football_updates.get_big_matches")
@patch("bot.football_updates.get_subscribers")
async def test_send_match_notifications_no_subscribers(mock_get_subscribers, mock_get_big_matches):
    """Test that no notifications are sent if there are no subscribers"""
    mock_get_big_matches.return_value = [
        ("Premier League", "Manchester United", "Chelsea", "2025-02-14T19:00:00Z")
    ]
    mock_get_subscribers.return_value = []  # No subscribers

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    await send_match_notifications(application_mock)

    bot_mock.send_message.assert_not_called()


@pytest.mark.asyncio
@patch("bot.football_updates.get_big_matches")
@patch("bot.football_updates.get_subscribers")
async def test_send_match_notifications_no_matches(mock_get_subscribers, mock_get_big_matches):
    """Test that no notifications are sent if there are no big matches"""
    mock_get_big_matches.return_value = []  # No big matches
    mock_get_subscribers.return_value = [123456789]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    await send_match_notifications(application_mock)

    bot_mock.send_message.assert_not_called()
