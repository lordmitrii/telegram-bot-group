"""Inline mode handler that answers queries with GPT-generated replies."""

import logging
import uuid
from typing import Optional

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
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


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer an inline query with a GPT-generated response to the typed text."""
    query = update.inline_query
    if query is None:
        return

    prompt = query.query.strip()
    if not prompt:
        await query.answer([], cache_time=0)
        return

    gpt_service = get_gpt_service()
    if not gpt_service.is_configured:
        await query.answer([], cache_time=0)
        return

    try:
        answer_text = await gpt_service.ask(prompt)
    except Exception:
        logging.exception("Failed to fetch GPT response for inline query")
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=MESSAGES["inline_gpt_error"],
                    input_message_content=InputTextMessageContent(
                        MESSAGES["inline_gpt_error"]
                    ),
                )
            ],
            cache_time=0,
        )
        return

    if not answer_text:
        await query.answer([], cache_time=0)
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=MESSAGES["inline_gpt_title"],
            description=answer_text[:200],
            input_message_content=InputTextMessageContent(answer_text[:4096]),
        )
    ]
    await query.answer(results, cache_time=0)
