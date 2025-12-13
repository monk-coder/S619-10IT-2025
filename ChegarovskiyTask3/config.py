"""
Конфигурация бота
Настройки приложения и игровые константы
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_NAME = "casino_bot.db"

STARTING_BALANCE = 1000
REFERRAL_BONUS = 10000
BONUS_AMOUNT = 500
BONUS_COOLDOWN = 10800  # 3 часа в секундах

EMOJI = {
    "dice": "🎲", "slot": "🎰", "cards": "🃏", "roulette": "🎡",
    "money": "💰", "trophy": "🏆", "back": "⬅️", "bonus": "🎁"
}
