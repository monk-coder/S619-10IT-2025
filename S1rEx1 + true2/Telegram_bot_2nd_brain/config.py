"""
Configuration file for the Telegram bot
"""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class BotConfig(BaseModel):
    model_config = {'protected_namespaces': ()}

    telegram_token: str = Field(default=os.getenv("TELEGRAM_BOT_TOKEN", ""))

    openrouter_api_key: str = Field(default=os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    model_name: str = Field(default="deepseek/deepseek-chat")

    database_url: str = Field(default=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db"))

    max_message_length: int = Field(default=4096)
    max_context_messages: int = Field(default=10)

    tesseract_cmd: Optional[str] = Field(default=os.getenv("TESSERACT_CMD", None))

    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    admin_users: list[int] = Field(
        default_factory=lambda: [int(uid) for uid in os.getenv("ADMIN_USERS", "").split(",") if uid]
    )


config = BotConfig()


def validate_config():
    """Validate that all critical configurations are set"""
    errors = []

    if not config.telegram_token:
        errors.append("TELEGRAM_BOT_TOKEN is not set")

    if not config.openrouter_api_key:
        errors.append("OPENROUTER_API_KEY is not set")

    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease create a .env file with the required variables:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("OPENROUTER_API_KEY=your_openrouter_api_key")
        return False

    return True
