"""Service for fetching today's holiday."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
from html.parser import HTMLParser
import logging
import re
from typing import List, Optional

import requests

from src.bot.core.config import get_settings
from src.bot.core.constants import MOSCOW_TZ

_RU_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


@dataclass(slots=True)
class Holiday:
    """Represents a holiday scraped from Calend.ru."""

    title: str
    description: str


class _CalendDayHTMLParser(HTMLParser):
    """Collect cleaned text tokens from a Calend.ru day page."""

    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self.tokens: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return

        cleaned = _clean_text(data)
        if not cleaned:
            return

        if self.tokens and self.tokens[-1] == cleaned:
            return

        self.tokens.append(cleaned)


def _clean_text(value: str) -> str:
    """Normalize scraped text."""
    return re.sub(r"\s+", " ", value).strip()


def _find_token_index(tokens: List[str], target: str, start: int = 0) -> int:
    """Find a token index by exact match."""
    for index in range(start, len(tokens)):
        if tokens[index] == target:
            return index
    return -1


def _looks_like_title(value: str) -> bool:
    """Check whether a token looks like a holiday title."""
    if len(value) < 5:
        return False
    if value.startswith("Image:"):
        return False
    if value.isdigit():
        return False
    if value in {"Праздники", "Международные праздники", "Праздники славян"}:
        return False
    if value.startswith(("Главная страница", "Адрес страницы:", "Сегодня", "Завтра")):
        return False
    if value.endswith("года") or "года," in value:
        return False
    return True


def _looks_like_description(value: str, title: str) -> bool:
    """Check whether a token looks like a holiday description."""
    if value == title:
        return False
    if len(value) < 25:
        return False
    if value.startswith("Image:"):
        return False
    if value in {"Международные праздники", "Праздники славян"}:
        return False
    if value.endswith("..."):
        return False
    return True


class HolidayService:
    """Fetch today's holiday from Calend.ru."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def get_todays_holiday(self) -> Optional[Holiday]:
        """Return a single holiday for today."""
        today = datetime.datetime.now(MOSCOW_TZ).date()
        url = self._settings.holiday_source_url_template.format(
            year=today.year,
            month=today.month,
            day=today.day,
        )

        try:
            response = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; telegram-bot/1.0; +https://telegram.org)"
                    )
                },
            )
            response.raise_for_status()
        except Exception as exc:
            logging.error(f"Error fetching today's holiday: {exc}")
            return None

        parser = _CalendDayHTMLParser()
        parser.feed(response.text)
        holiday = self._extract_holiday(parser.tokens, today)
        if holiday is not None:
            return holiday

        logging.warning("Could not parse any holiday items from source page.")
        return None

    def _extract_holiday(
        self, tokens: List[str], today: datetime.date
    ) -> Optional[Holiday]:
        """Extract the first holiday title and description from parsed tokens."""
        date_heading = f"{today.day} {_RU_MONTHS[today.month]} {today.year} года"
        section_start = _find_token_index(tokens, date_heading)
        if section_start == -1:
            return None

        holidays_heading = _find_token_index(tokens, "Праздники", start=section_start)
        if holidays_heading == -1:
            return None

        title = None
        description = None
        for token in tokens[holidays_heading + 1 :]:
            if token in {"Именины", "Хроника", "Народный календарь"}:
                break

            if title is None and _looks_like_title(token):
                title = token
                continue

            if title is not None and _looks_like_description(token, title):
                description = token
                break

        if title and description:
            return Holiday(title=title, description=description)

        return None


_service: Optional[HolidayService] = None


def _get_service() -> HolidayService:
    global _service
    if _service is None:
        _service = HolidayService()
    return _service


async def get_todays_holiday() -> Optional[Holiday]:
    """Module-level wrapper for fetching today's holiday."""
    return await _get_service().get_todays_holiday()
