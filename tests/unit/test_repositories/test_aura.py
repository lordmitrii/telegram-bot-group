"""Tests for aura repository."""

from src.bot.repositories.aura import AuraRepository


def test_change_and_get_aura(test_db):
    """Aura points should accumulate for the same user."""
    repo = AuraRepository(test_db)

    repo.change_points(chat_id=123, person_name="test_user", points=200)
    repo.change_points(chat_id=123, person_name="test_user", points=-50)

    aura = repo.get_aura(chat_id=123, person_name="test_user")

    assert aura.aura_points == 150
