import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    DB_NAME = os.getenv('DB_NAME', 'secret_santa.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен в .env файле")