"""Notification service for sending messages to subscribers."""

import logging
from typing import List, Optional

from telegram.ext import Application

from src.bot.repositories.subscriber import SubscriberRepository


class NotificationService:
    """Service for sending notifications to subscribers."""

    def __init__(
        self,
        application: Application,
        subscriber_repo: Optional[SubscriberRepository] = None,
    ):
        self._application = application
        self._subscriber_repo = subscriber_repo or SubscriberRepository()

    async def send_to_all_subscribers(
        self,
        message: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False,
    ) -> int:
        """Send a message to all subscribers.

        Args:
            message: The message to send
            parse_mode: Optional parse mode (e.g., "Markdown")
            disable_web_page_preview: Whether to disable link previews

        Returns:
            Number of successfully sent messages
        """
        subscribers = self._subscriber_repo.get_all_chat_ids()
        if not subscribers:
            logging.info("No subscribers to notify.")
            return 0

        sent_count = 0
        for chat_id in subscribers:
            try:
                await self._application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Error sending message to {chat_id}: {e}")

        return sent_count

    async def send_to_chat(
        self,
        chat_id: int,
        message: str,
        parse_mode: Optional[str] = None,
    ) -> bool:
        """Send a message to a specific chat.

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self._application.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logging.error(f"Error sending message to {chat_id}: {e}")
            return False

    def get_subscriber_count(self) -> int:
        """Get the total number of subscribers."""
        return len(self._subscriber_repo.get_all_chat_ids())
