"""Service for fetching today's holiday."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import logging
import re
from typing import List, Optional

import requests

from src.bot.core.config import get_settings


@dataclass(slots=True)
class Holiday:
    """Represents a holiday item scraped from the source page."""

    title: str
    description: str


class _TodayHolidayHTMLParser(HTMLParser):
    """Extract holiday cards from daysoftheyear.com/today/."""

    def __init__(self) -> None:
        super().__init__()
        self._capture_title = False
        self._awaiting_description = False
        self._current_title: List[str] = []
        self._current_description: List[str] = []
        self.holidays: List[Holiday] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag == "h3":
            self._flush_holiday()
            self._capture_title = True
            self._awaiting_description = False
            self._current_title = []
            self._current_description = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3":
            self._capture_title = False
            self._awaiting_description = bool(self._current_title)

        if tag in {"h2", "section", "article", "li"}:
            self._flush_holiday()

    def handle_data(self, data: str) -> None:
        cleaned = _clean_text(data)
        if not cleaned:
            return

        if self._capture_title:
            self._current_title.append(cleaned)
            return

        if self._awaiting_description and self._looks_like_description(cleaned):
            self._current_description.append(cleaned)
            self._flush_holiday()

    def _flush_holiday(self) -> None:
        if not self._current_title or not self._current_description:
            return

        title = _clean_text(" ".join(self._current_title))
        description = _clean_text(" ".join(self._current_description))
        if not title or not description:
            return

        if any(existing.title == title for existing in self.holidays):
            return

        self.holidays.append(Holiday(title=title, description=description))
        self._current_title = []
        self._current_description = []
        self._awaiting_description = False

    def close(self) -> None:
        """Flush the last parsed holiday before closing."""
        self._flush_holiday()
        super().close()

    @staticmethod
    def _looks_like_description(value: str) -> bool:
        """Filter out dates and layout text between heading and description."""
        lowered = value.lower()
        if lowered.startswith(("mon ", "tue ", "wed ", "thu ", "fri ", "sat ", "sun ")):
            return False
        if lowered.startswith("image:"):
            return False
        if value.endswith("..."):
            return False
        return len(value) >= 20


def _clean_text(value: str) -> str:
    """Normalize scraped text."""
    without_tags = re.sub(r"\s+", " ", value)
    return without_tags.strip()


class HolidayService:
    """Fetch today's holiday from the configured source."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def get_todays_holiday(self) -> Optional[Holiday]:
        """Return a single holiday for today."""
        try:
            response = requests.get(
                self._settings.holiday_source_url,
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

        parser = _TodayHolidayHTMLParser()
        parser.feed(response.text)
        parser.close()

        for holiday in parser.holidays:
            if len(holiday.title) < 3 or len(holiday.description) < 20:
                continue
            return holiday

        logging.warning("Could not parse any holiday items from source page.")
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
