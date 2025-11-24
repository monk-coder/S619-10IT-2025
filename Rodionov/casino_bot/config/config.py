# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

    # ⚠️ ЗАМЕНИТЕ 123456789 НА ВАШ РЕАЛЬНЫЙ ID ⚠️
    # Чтобы узнать ваш ID:
    # 1. Запустите get_my_id.py
    # 2. Отправьте боту команду /id
    # 3. Скопируйте ваш ID и вставьте сюда
    ADMIN_IDS = [5631945112]  # ← ЗАМЕНИТЕ ЭТО ЧИСЛО

    # Настройки игр
    INITIAL_BALANCE = 1000
    MIN_BET = 10
    MAX_BET = 1000

    # Настройки слотов
    SLOTS_SYMBOLS = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    SLOTS_PAYOUTS = {
        'three_7️⃣': 10,
        'three_💎': 8,
        'three_🔔': 5,
        'three_any': 3,
        'two_any': 2
    }

    # Настройки костей
    DICE_MULTIPLIER = 2

    # Настройки рулетки
    ROULETTE_NUMBERS = list(range(0, 37))
    ROULETTE_COLORS = {
        'red': [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
        'black': [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35],
        'green': [0]
    }