from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


@dataclass(slots=True)
class Settings:
    bot_token: str
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_site_url: str | None
    database_path: Path
    ocr_language: str


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1:free")
    openrouter_site_url = os.getenv("OPENROUTER_SITE_URL")
    database_path = Path(os.getenv("DATABASE_PATH", BASE_DIR / "notes.db"))
    ocr_language = os.getenv("OCR_LANGUAGE", "eng")

    return Settings(
        bot_token=bot_token,
        openrouter_api_key=openrouter_key.strip() if openrouter_key else None,
        openrouter_model=openrouter_model.strip(),
        openrouter_site_url=openrouter_site_url.strip() if openrouter_site_url else None,
        database_path=database_path,
        ocr_language=ocr_language,
    )
