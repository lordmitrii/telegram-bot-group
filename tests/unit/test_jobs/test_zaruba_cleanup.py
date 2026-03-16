"""Tests for zaruba cleanup job."""

import pytest
from unittest.mock import AsyncMock

import src.bot.repositories.session as session_module
from src.bot.jobs.zaruba_cleanup import auto_cancel_zarubas
from src.bot.models.user import ChatUser
from src.bot.repositories.aura import AuraRepository
from src.bot.repositories.session import SessionRepository
from src.bot.repositories.user_identity import UserIdentityRepository
from src.bot.repositories.zaruba import ZarubaStatsRepository
from src.bot.services.zaruba import ZarubaService


def make_user(user_id: int, name: str) -> ChatUser:
    """Create a stable chat user for tests."""
    return ChatUser(user_id=user_id, display_name=name, username=name)


@pytest.mark.asyncio
async def test_auto_cancel_zarubas_applies_nightly_absence_penalty(test_db):
    """Nightly cleanup should penalize unregistered users once, by user ID."""
    session_repo = SessionRepository(test_db)
    service = ZarubaService(
        session_repo=session_repo,
        stats_repo=ZarubaStatsRepository(test_db),
        aura_repo=AuraRepository(test_db),
        user_repo=UserIdentityRepository(test_db),
    )
    service.create_zaruba(chat_id=123456, time="18:00", creator=make_user(1, "creator"))

    context = AsyncMock()
    context.bot.username = "test_bot"

    creator_member = AsyncMock()
    creator_member.user.id = 1
    creator_member.user.username = "creator"
    creator_member.user.first_name = "Creator"

    skipped_member = AsyncMock()
    skipped_member.user.id = 2
    skipped_member.user.username = "ghost"
    skipped_member.user.first_name = "Ghost"

    context.bot.get_chat_administrators = AsyncMock(
        return_value=[creator_member, skipped_member]
    )

    original_repo = session_module._default_repo
    session_module._default_repo = session_repo
    try:
        await auto_cancel_zarubas(context)
    finally:
        session_module._default_repo = original_repo

    assert service.get_user_aura(123456, user_id=2, username="ghost").aura_points == -5
    assert service.get_session(123456) is None
