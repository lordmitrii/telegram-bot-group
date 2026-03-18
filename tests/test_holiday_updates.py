"""Tests for holiday service and daily notifications."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
                <section>
                    <div class="holiday">18 марта</div>
                    <a href="/nameday/" class="btntitle">Именины</a>
                    <ul class="itemsNet">
                        <li class="three-three">
                            <div class="caption">
                                <span class="title">
                                    <a href="https://www.calend.ru/holidays/0/0/9999/">Лишний праздник</a>
                                </span>
                                <p class="descr descrFixed">
                                    <a href="https://www.calend.ru/holidays/0/0/9999/">
                                        Это не тот блок.
                                    </a>
                                </p>
                            </div>
                        </li>
                    </ul>
                </section>
                <section>
                    <div class="holiday">18 марта</div>
                    <a href="/holidays/" class="btntitle">Праздники</a>
                    <ul class="itemsNet">
                        <li class="three-three">
                            <div class="caption">
                                <span class="title">
                                    <a href="https://www.calend.ru/holidays/0/0/3282/">
                                        День воссоединения Крыма с Россией
                                    </a>
                                </span>
                                <p class="descr descrFixed">
                                    <a href="https://www.calend.ru/holidays/0/0/3282/">
                                        18 марта в Российской Федерации отмечается День воссоединения Крыма с Россией. На территории Республики Крым этот день является праздничным и выходным согласно республиканскому закону № 80-ЗРК/2015 от 3 марта 2015 года. В Севастополе дата 18 марта называется Днем возвращения города Севастополя в Россию. Дополнительный хвост...
                                    </a>
                                    <span class="theFog"></span>
                                </p>
                            </div>
                        </li>
                    </ul>
                </section>
            </body>
        </html>
    """
    mock_get.return_value = mock_response

    holiday = await get_todays_holiday()

    assert holiday == Holiday(
        title="День воссоединения Крыма с Россией",
        description=(
            "18 марта в Российской Федерации отмечается День воссоединения Крыма с Россией. "
            "На территории Республики Крым этот день является праздничным и выходным "
            "согласно республиканскому закону № 80-ЗРК/2015 от 3 марта 2015 года. "
            "В Севастополе дата 18 марта называется Днем возвращения города Севастополя "
            "в Россию."
        ),
    )


@pytest.mark.asyncio
@patch("src.bot.services.holiday.requests.get")
async def test_get_todays_holiday_skips_truncated_second_sentence(mock_get):
    """Test that truncated sentences are excluded from the final summary."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.text = """
        <html>
            <body>
                <div class="holiday">18 марта</div>
                <a href="/holidays/" class="btntitle">Праздники</a>
                <ul class="itemsNet">
                    <li class="three-three">
                        <div class="caption">
                            <span class="title">
                                <a href="https://www.calend.ru/holidays/0/0/1284/">
                                    День внутренних войск Беларуси
                                </a>
                            </span>
                            <p class="descr descrFixed">
                                <a href="https://www.calend.ru/holidays/0/0/1284/">
                                    18 марта в Белоруссии празднуют День внутренних войск. На территории современной Беларуси в разные периоды истории всегда существовали...
                                </a>
                            </p>
                        </div>
                    </li>
                </ul>
            </body>
        </html>
    """
    mock_get.return_value = mock_response

    holiday = await get_todays_holiday()

    assert holiday == Holiday(
        title="День внутренних войск Беларуси",
        description="18 марта в Белоруссии празднуют День внутренних войск.",
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
