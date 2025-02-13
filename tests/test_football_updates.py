import pytest
from unittest.mock import AsyncMock, patch
from bot.football_updates import get_big_matches, get_subscribers, subscribe, unsubscribe, send_match_notifications, add_subscriber
from bot.messages import MESSAGES

@pytest.mark.asyncio
@patch("bot.football_updates.fetch_fixtures")
async def test_get_big_matches(mock_fetch_fixtures):
    """Test if get_big_matches correctly identifies big matches with fuzzy matching"""

    mock_fetch_fixtures.return_value = [
        {
            "competition": {"name": "Premier League"},
            "homeTeam": {"name": "Manchester Utd"},
            "awayTeam": {"name": "Liverpool"},
            "utcDate": "2024-02-14T18:00:00Z"
        },
        {
            "competition": {"name": "Premier League"},
            "homeTeam": {"name": "Manchester United"},  # Slightly different format
            "awayTeam": {"name": "Chelsea"},
            "utcDate": "2024-02-14T20:00:00Z"
        },
        {
            "competition": {"name": "La Liga"},
            "homeTeam": {"name": "Real Madrid"},
            "awayTeam": {"name": "Barcelona"},
            "utcDate": "2024-02-14T21:00:00Z"
        },
        {
            "competition": {"name": "Bundesliga"},
            "homeTeam": {"name": "FC Bayern"},
            "awayTeam": {"name": "Borussia Dortmund"},
            "utcDate": "2024-02-14T22:00:00Z"
        },
        {
            "competition": {"name": "Serie A"},
            "homeTeam": {"name": "Juventus"},  # Not in the LEAGUES list
            "awayTeam": {"name": "Inter Milan"},
            "utcDate": "2024-02-14T23:00:00Z"
        }
    ]

    expected_matches = [
        ("Premier League", "Manchester Utd", "Liverpool", "2024-02-14T18:00:00Z"),
        ("Premier League", "Manchester United", "Chelsea", "2024-02-14T20:00:00Z"),
        ("La Liga", "Real Madrid", "Barcelona", "2024-02-14T21:00:00Z"),
        ("Bundesliga", "FC Bayern", "Borussia Dortmund", "2024-02-14T22:00:00Z"),
    ]

    matches = await get_big_matches()
    assert matches == expected_matches, f"Expected {expected_matches}, but got {matches}"


@pytest.mark.asyncio
@patch("bot.football_updates.fetch_fixtures")
async def test_get_big_matches_no_matches(mock_fetch_fixtures):
    """Test when no matches should be returned"""
    
    mock_fetch_fixtures.return_value = [
        {
            "competition": {"name": "Some Random League"},
            "homeTeam": {"name": "Random FC"},
            "awayTeam": {"name": "Unknown United"},
            "utcDate": "2024-02-14T18:00:00Z"
        }
    ]

    matches = await get_big_matches()
    assert matches == [], f"Expected an empty list, but got {matches}"


@pytest.mark.asyncio
@patch("bot.football_updates.fetch_fixtures")
async def test_get_big_matches_ucl(mock_fetch_fixtures):
    """Test if UEFA Champions League matches are always included"""
    
    mock_fetch_fixtures.return_value = [
        {
            "competition": {"name": "UEFA Champions League"},
            "homeTeam": {"name": "Some Unknown Team"},
            "awayTeam": {"name": "Another Unknown Team"},
            "utcDate": "2024-02-14T19:00:00Z"
        }
    ]

    matches = await get_big_matches()
    assert len(matches) == 1
    assert matches[0][0] == "UEFA Champions League"


@pytest.mark.asyncio
async def test_subscribe():
    """Test the /subscribe command."""
    update = AsyncMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context = AsyncMock()

    await subscribe(update, context)
    update.message.reply_text.assert_called_once_with(MESSAGES["subscribe"])
    assert 12345 in get_subscribers()

@pytest.mark.asyncio
async def test_unsubscribe():
    """Test the /unsubscribe command."""
    add_subscriber(12345)
    update = AsyncMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context = AsyncMock()

    await unsubscribe(update, context)
    update.message.reply_text.assert_called_once_with(MESSAGES["unsubscribe"])
    assert 12345 not in get_subscribers()

@pytest.mark.asyncio
@patch("bot.football_updates.get_big_matches", return_value=[("Premier League", "Man Utd", "Liverpool", "2024-02-14T18:00:00Z")])
@patch("bot.football_updates.get_subscribers", return_value=[12345])
async def test_send_match_notifications(mock_get_big_matches, mock_get_subscribers):
    """Test sending notifications to subscribers."""
    application = AsyncMock()
    application.bot.send_message = AsyncMock()

    await send_match_notifications(application)
    application.bot.send_message.assert_called_once()

