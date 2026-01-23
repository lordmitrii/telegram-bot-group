import logging
import re
from dataclasses import dataclass
from typing import Dict, List

import requests
from telegram.ext import Application, ContextTypes

from bot.config import SCRAPER_POLL_INTERVAL_SECONDS
from bot.db.repositories import get_subscribers


@dataclass
class ScraperConfig:
    name: str
    url: str
    regex: str
    threshold: int


SCRAPER_STATES: Dict[str, int] = {}

SCRAPERS: List[ScraperConfig] = [
    ScraperConfig(
        name="Cairngorm Mountain",
        url="https://cairngormmountain.skiperformance.com/en/ajax/html/shop_widget_buy/viewable_buy_option?skugroup_id=2415&has_only_one_object=0&object_id=17234&object_type=Product&product_ids=%5B%2217234%22%5D&family=grid&promo_connector_id=&promo_id=&has_more_than_one_tab=true&is_details=1&is_promo=0&is_promo_offer=0&key=p_17234&product_ids%5B0%5D=17234&not_remove_body_grid_class=1&validity_start=05%2F01%2F2026&wid_id_start=0&_=1767529386986",
        regex=r"data-available_qty=['\"]?(\d+)",
        threshold=1,
    )
]


def _parse_qty(html: str, regex: str) -> int:
    """Parses quantity from html using provided regex."""
    match = re.search(regex, html)
    return int(match.group(1)) if match else 0


def _fetch_quantity(scraper: ScraperConfig) -> int:
    try:
        response = requests.get(scraper.url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        logging.error("Error fetching scraper %s: %s", scraper.name, exc)
        return 0

    try:
        return _parse_qty(response.text, scraper.regex)
    except Exception as exc:
        logging.error("Error parsing scraper %s response: %s", scraper.name, exc)
        return 0


async def poll_scrapers(context: ContextTypes.DEFAULT_TYPE):
    """Poll configured scrapers and notify subscribers when they become available."""
    application = context.job.data
    subscribers = get_subscribers()
    if not subscribers:
        logging.info("No subscribers for scraper notifications.")
        return

    for scraper in SCRAPERS:
        current_qty = _fetch_quantity(scraper)
        previous_qty = SCRAPER_STATES.get(scraper.name, 0)

        is_available = current_qty > scraper.threshold
        was_available = previous_qty > scraper.threshold
        SCRAPER_STATES[scraper.name] = current_qty

        if not is_available or was_available:
            continue

        message = f"🔔 {scraper.name}: {current_qty} items available! {scraper.url}"
        for chat_id in subscribers:
            try:
                await application.bot.send_message(
                    chat_id=chat_id, text=message, disable_web_page_preview=True
                )
            except Exception as exc:
                logging.error("Error sending scraper update to %s: %s", chat_id, exc)


def schedule_scraper_polling(application: Application):
    """Schedule scraper polling so it's easy to plug in more scrapers."""
    if application.job_queue.get_jobs_by_name("scraper_polling"):
        return

    interval = max(60, SCRAPER_POLL_INTERVAL_SECONDS)
    application.job_queue.run_repeating(
        poll_scrapers,
        interval=interval,
        first=5,
        name="scraper_polling",
        data=application,
    )
