"""Handler that replies with a GPT-generated response when the bot is @mentioned."""

import logging
import re
from typing import List, Optional

from telegram import Message, MessageEntity, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from src.bot.i18n.messages import MESSAGES
from src.bot.services.gpt import GPTService

_gpt_service: Optional[GPTService] = None


def get_gpt_service() -> GPTService:
    """Get the shared GPTService instance, creating it on first use."""
    global _gpt_service
    if _gpt_service is None:
        _gpt_service = GPTService()
    return _gpt_service


def _extract_mention_prompt(
    text: str, entities: List[MessageEntity], bot_username: str
) -> Optional[str]:
    """Return the message text with the bot's @mention stripped, or None if not mentioned."""
    mention = f"@{bot_username}"
    mentioned = any(
        entity.type == MessageEntity.MENTION
        and text[entity.offset : entity.offset + entity.length].lower()
        == mention.lower()
        for entity in entities
    )
    if not mentioned:
        return None

    return re.sub(re.escape(mention), "", text, count=1, flags=re.IGNORECASE).strip()


async def mention_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with a GPT-generated response when the bot is @mentioned in a message."""
    message: Optional[Message] = update.message
    if message is None or not message.text or not message.entities:
        return

    bot_username = context.bot.username
    if not bot_username:
        return

    prompt = _extract_mention_prompt(message.text, message.entities, bot_username)
    if not prompt:
        return

    gpt_service = get_gpt_service()
    if not gpt_service.is_configured:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    try:
        answer_text = await gpt_service.ask(prompt)
    except Exception:
        logging.exception("Failed to fetch GPT response for mention")
        await message.reply_text(MESSAGES["gpt_error"])
        return

    if not answer_text:
        return

    await message.reply_text(answer_text)
