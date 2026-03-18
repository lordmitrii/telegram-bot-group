"""Service for fetching today's holiday."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import logging
import re
from typing import Dict, Iterable, List, Optional

import requests

from src.bot.core.config import get_settings

_FULL_SENTENCE_RE = re.compile(r"[^.!?]*[.!?](?=\s|$)")


@dataclass(slots=True)
class Holiday:
    """Represents a holiday scraped from Calend.ru."""

    title: str
    description: str


@dataclass(slots=True)
class _Node:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List["_Node"] = field(default_factory=list)
    texts: List[str] = field(default_factory=list)

    def append_text(self, value: str) -> None:
        cleaned = _clean_text(value)
        if cleaned:
            self.texts.append(cleaned)

    def text_content(self) -> str:
        parts = list(self.texts)
        for child in self.children:
            child_text = child.text_content()
            if child_text:
                parts.append(child_text)
        return _clean_text(" ".join(parts))

    def class_names(self) -> set[str]:
        return set(self.attrs.get("class", "").split())


class _CalendRootHTMLParser(HTMLParser):
    """Build a lightweight DOM tree from the Calend.ru homepage."""

    def __init__(self) -> None:
        super().__init__()
        self.root = _Node(tag="document")
        self._stack: List[_Node] = [self.root]
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1

        node = _Node(
            tag=tag,
            attrs={key: value or "" for key, value in attrs},
        )
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                break

        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        self._stack[-1].append_text(data)


def _clean_text(value: str) -> str:
    """Normalize scraped text."""
    return re.sub(r"\s+", " ", value).strip()


def _iter_nodes(node: _Node) -> Iterable[_Node]:
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _find_first(
    node: _Node,
    *,
    tag: Optional[str] = None,
    class_name: Optional[str] = None,
) -> Optional[_Node]:
    for child in _iter_nodes(node):
        if tag is not None and child.tag != tag:
            continue
        if class_name is not None and class_name not in child.class_names():
            continue
        return child
    return None


def _find_all(
    node: _Node,
    *,
    tag: Optional[str] = None,
    class_name: Optional[str] = None,
) -> List[_Node]:
    matches: List[_Node] = []
    for child in _iter_nodes(node):
        if tag is not None and child.tag != tag:
            continue
        if class_name is not None and class_name not in child.class_names():
            continue
        matches.append(child)
    return matches


def _contains_holiday_cards(node: _Node) -> bool:
    for item in _find_all(node, tag="li"):
        if _find_first(item, tag="span", class_name="title") and _find_first(
            item, tag="p", class_name="descr"
        ):
            return True
    return False


def _find_list_in_node(node: _Node) -> Optional[_Node]:
    for candidate in _find_all(node, tag="ul", class_name="itemsNet"):
        if _contains_holiday_cards(candidate):
            return candidate
    return None


def _find_holiday_list(root: _Node) -> Optional[_Node]:
    for parent in _iter_nodes(root):
        children = parent.children
        for index, child in enumerate(children):
            if child.tag != "div" or "holiday" not in child.class_names():
                continue

            if index + 2 >= len(children):
                continue

            next_child = children[index + 1]
            if next_child.tag != "a":
                continue
            if next_child.attrs.get("href") != "/holidays/":
                continue
            if "btntitle" not in next_child.class_names():
                continue
            if next_child.text_content() != "Праздники":
                continue

            for candidate in children[index + 2 :]:
                holiday_list = _find_list_in_node(candidate)
                if holiday_list is not None:
                    return holiday_list

    for candidate in _find_all(root, tag="ul", class_name="itemsNet"):
        if _contains_holiday_cards(candidate):
            return candidate

    return None


def _extract_holidays(holiday_list: _Node) -> List[Holiday]:
    holidays: List[Holiday] = []
    for child in holiday_list.children:
        if child.tag != "li":
            continue

        title_node = _find_first(child, tag="span", class_name="title")
        description_node = _find_first(child, tag="p", class_name="descr")

        if title_node is None or description_node is None:
            continue

        title_link = _find_first(title_node, tag="a")
        description_link = _find_first(description_node, tag="a")

        title = (
            title_link.text_content()
            if title_link is not None
            else title_node.text_content()
        )
        description_source = (
            description_link.text_content()
            if description_link is not None
            else description_node.text_content()
        )
        summary = _summarize_description(description_source)

        if title and summary:
            holidays.append(Holiday(title=title, description=summary))

    return holidays


def _summarize_description(text: str) -> str:
    """Keep up to the first three complete sentences and adapt to minor HTML text issues."""
    cleaned = _clean_text(text)
    if not cleaned:
        return ""

    # Calend.ru sometimes omits a space after sentence punctuation in truncated previews.
    cleaned = re.sub(r"([.!?])([A-ZА-ЯЁ])", r"\1 \2", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)

    sentences = [_clean_text(match.group(0)) for match in _FULL_SENTENCE_RE.finditer(cleaned)]
    if not sentences:
        return ""

    summary = " ".join(sentences[:3]).strip()
    summary = re.sub(r"\s+([,.;:!?])", r"\1", summary)
    summary = re.sub(r"([.!?])(?:\s*\.)+$", r"\1", summary)
    if summary:
        return summary

    return ""


class HolidayService:
    """Fetch today's holiday from Calend.ru."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def get_todays_holiday(self) -> Optional[Holiday]:
        """Return a single holiday for today."""
        url = self._settings.holiday_source_url_template

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

        parser = _CalendRootHTMLParser()
        parser.feed(response.text)

        holiday_list = _find_holiday_list(parser.root)
        if holiday_list is None:
            logging.warning("Could not find the holidays block on source page.")
            return None

        holidays = _extract_holidays(holiday_list)
        if holidays:
            return holidays[0]

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
