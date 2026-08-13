"""GPT service for generating chat completions via the OpenAI API."""

from typing import Optional

from openai import AsyncOpenAI

from src.bot.core.config import get_settings

SYSTEM_PROMPT = (
    "Ты — Жека, бот чата «Пем Бравл Старс». Ты не ассистент, а один из "
    "своих: пишешь как друг в переписке, а не как справочная служба.\n\n"
    "Стиль:\n"
    "- Коротко и живо: 1-3 предложения, без вступлений и канцелярита.\n"
    "- Без фраз вроде «как ИИ-модель», «я не могу предоставить» — ты Жека, "
    "а не корпоративный бот.\n"
    "- Можно шутить, подкалывать, нести добродушную чушь, если вопрос "
    "несерьёзный или в чате есть вайб — точность в этом случае не важна.\n"
    "- Уместно ввернуть местный сленг чата: братва, заруба, аура, "
    "нубик, вафлежуй, — но не через слово, только когда органично.\n\n"
    "Но если вопрос реально важный (учёба, работа, деньги, помощь по "
    "делу) — отвечай по существу и полезно, без придурковатости.\n\n"
    "Отвечай на русском, если не попросили иначе."
)


class GPTService:
    """Service for generating text responses using the OpenAI API."""

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[AsyncOpenAI] = (
            AsyncOpenAI(api_key=self._settings.openai_api_key)
            if self._settings.openai_api_key
            else None
        )

    @property
    def is_configured(self) -> bool:
        """Return whether an OpenAI API key is configured."""
        return self._client is not None

    async def ask(self, prompt: str) -> str:
        """Send a prompt to OpenAI and return the reply text."""
        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured")

        response = await self._client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()
