"""Scraper service for monitoring external resources."""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class ScraperConfig:
    """Configuration for a scraper."""

    name: str
    url: str
    regex: str
    threshold: int


class ScraperService:
    """Service for scraping and monitoring external resources."""

    def __init__(self, scrapers: Optional[List[ScraperConfig]] = None):
        self._scrapers = scrapers or self._default_scrapers()
        self._states: Dict[str, int] = {}

    @staticmethod
    def _default_scrapers() -> List[ScraperConfig]:
        """Get default scraper configurations."""
        return [
            ScraperConfig(
                name="Cairngorm Mountain",
                url="https://cairngormmountain.skiperformance.com/en/ajax/html/shop_widget_buy/viewable_buy_option?skugroup_id=2415&has_only_one_object=0&object_id=17234&object_type=Product&product_ids=%5B%2217234%22%5D&family=grid&promo_connector_id=&promo_id=&has_more_than_one_tab=true&is_details=1&is_promo=0&is_promo_offer=0&key=p_17234&product_ids%5B0%5D=17234&not_remove_body_grid_class=1&validity_start=05%2F01%2F2026&wid_id_start=0&_=1767529386986",
                regex=r"data-available_qty=['\"]?(\d+)",
                threshold=1,
            )
        ]

    def _parse_quantity(self, html: str, regex: str) -> int:
        """Parse quantity from HTML using regex."""
        match = re.search(regex, html)
        return int(match.group(1)) if match else 0

    def _fetch_quantity(self, scraper: ScraperConfig) -> int:
        """Fetch quantity from a scraper URL."""
        try:
            response = requests.get(scraper.url, timeout=10)
            response.raise_for_status()
            return self._parse_quantity(response.text, scraper.regex)
        except Exception as exc:
            logging.error("Error fetching scraper %s: %s", scraper.name, exc)
            return 0

    def check_availability(
        self,
    ) -> List[tuple]:
        """Check all scrapers for availability changes.

        Returns:
            List of (scraper_name, quantity, url) for newly available items
        """
        notifications: List[tuple] = []

        for scraper in self._scrapers:
            current_qty = self._fetch_quantity(scraper)
            previous_qty = self._states.get(scraper.name, 0)

            is_available = current_qty > scraper.threshold
            was_available = previous_qty > scraper.threshold
            self._states[scraper.name] = current_qty

            if is_available and not was_available:
                notifications.append((scraper.name, current_qty, scraper.url))

        return notifications

    def get_state(self, name: str) -> int:
        """Get the current state for a scraper."""
        return self._states.get(name, 0)

    def set_state(self, name: str, value: int) -> None:
        """Set the state for a scraper."""
        self._states[name] = value


# Module-level state for backwards compatibility
SCRAPER_STATES: Dict[str, int] = {}
SCRAPERS: List[ScraperConfig] = [
    ScraperConfig(
        name="Cairngorm Mountain",
        url="https://cairngormmountain.skiperformance.com/en/ajax/html/shop_widget_buy/viewable_buy_option?skugroup_id=2415&has_only_one_object=0&object_id=17234&object_type=Product&product_ids=%5B%2217234%22%5D&family=grid&promo_connector_id=&promo_id=&has_more_than_one_tab=true&is_details=1&is_promo=0&is_promo_offer=0&key=p_17234&product_ids%5B0%5D=17234&not_remove_body_grid_class=1&validity_start=05%2F01%2F2026&wid_id_start=0&_=1767529386986",
        regex=r"data-available_qty=['\"]?(\d+)",
        threshold=1,
    )
]
