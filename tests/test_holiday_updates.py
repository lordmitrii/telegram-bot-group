"""Tests for holiday service and daily notifications."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz

from src.bot.jobs.holiday import send_holiday_notifications
from src.bot.services.holiday import Holiday, get_todays_holiday


@pytest.mark.asyncio
@patch("src.bot.services.holiday.requests.get")
async def test_get_todays_holiday_success(mock_get):
    """Test that a holiday card is parsed from the source page."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.text = """
        <html>
            <body>
                <h1>17 марта 2026 года</h1>
                <div>Праздники</div>
                <div>Всемирный день социальной работы</div>
                <div>2026</div>
                <div>«Всемирный день социальной работы» отмечается в 3-й вторник марта.</div>
                <div>Международные праздники</div>
                <div>Каждый год в третий вторник марта отмечается Всемирный день социальной работы.</div>
            </body>
        </html>
    """
    mock_get.return_value = mock_response

    fake_now = datetime(2026, 3, 17, 12, 0, tzinfo=pytz.timezone("Europe/Moscow"))
    with patch("src.bot.services.holiday.datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now
        holiday = await get_todays_holiday()

    assert holiday == Holiday(
        title="Всемирный день социальной работы",
        description="«Всемирный день социальной работы» отмечается в 3-й вторник марта.",
    )


@pytest.mark.asyncio
@patch("src.bot.services.holiday.requests.get")
async def test_get_todays_holiday_failure(mock_get):
    """Test that fetch errors return no holiday."""
    mock_get.side_effect = RuntimeError("boom")

    holiday = await get_todays_holiday()

    assert holiday is None


@pytest.mark.asyncio
@patch("src.bot.jobs.holiday.HolidayService")
@patch("src.bot.jobs.holiday.get_subscribers")
async def test_send_holiday_notifications(mock_get_subscribers, mock_service_class):
    """Test sending the holiday notification to all subscribers."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service

    async def async_get_todays_holiday():
        return Holiday(
            title="Beer Day",
            description="An excellent excuse to gather the chat and crack something open.",
        )

    mock_service.get_todays_holiday = async_get_todays_holiday
    mock_get_subscribers.return_value = [123456789, 987654321]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_holiday_notifications(fake_context)

    assert bot_mock.send_message.call_count == 2


@pytest.mark.asyncio
@patch("src.bot.jobs.holiday.HolidayService")
@patch("src.bot.jobs.holiday.get_subscribers")
async def test_send_holiday_notifications_no_holiday(
    mock_get_subscribers, mock_service_class
):
    """Test that nothing is sent when no holiday is available."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service

    async def async_get_todays_holiday():
        return None

    mock_service.get_todays_holiday = async_get_todays_holiday
    mock_get_subscribers.return_value = [123456789]

    application_mock = AsyncMock()
    bot_mock = AsyncMock()
    application_mock.bot = bot_mock

    fake_context = AsyncMock()
    fake_context.job.data = application_mock

    await send_holiday_notifications(fake_context)

    bot_mock.send_message.assert_not_called()
