import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "clicker_game.db")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

    # Настройки игры
    BASE_ENERGY = 100
    ENERGY_RECOVERY_RATE = 1
    AUTO_CLICKER_INTERVAL = 1