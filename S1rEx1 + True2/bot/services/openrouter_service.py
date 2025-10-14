from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


DEFAULT_PROMPT = (
    "Составь структурированный конспект по теме {topic}. "
    "Используй заголовки, списки и короткие объяснения ключевых идей."
)


@dataclass(slots=True)
class OpenRouterService:
    api_key: str | None
    model: str = "deepseek/deepseek-r1:free"
    site_url: str | None = None

    def __post_init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate_note(self, topic: str, template: str | None = None) -> str:
        if not self.is_configured():
            raise RuntimeError("OpenRouter API key is not configured")

        if self._client is None:
            await self.start()
        assert self._client is not None

        prompt = (template or DEFAULT_PROMPT).format(topic=topic.strip())

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
            headers["X-Title"] = "Digital Brain Bot"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты создаёшь компактные, полезные конспекты и учебные материалы.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        response = await self._client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenRouter вернул пустой ответ")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            # Responses API can return mixed content segments
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        if not content:
            raise RuntimeError("Не удалось получить текст ответа от модели")

        return content.strip()
