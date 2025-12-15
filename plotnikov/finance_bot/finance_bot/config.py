"""Конфигурация бота"""
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВПИШИ_СВОЙ_ТОКЕН_ЗДЕСЬ")

DB_PATH = os.environ.get(
    "FINANCE_TRACKER_DB",
    os.path.join(os.path.dirname(__file__), "finance_tracker.sqlite3")
)

# Категории расходов
EXPENSE_CATEGORIES = (
    ("food", "🍔", "Еда"),
    ("transport", "🚌", "Транспорт"),
    ("entertainment", "🎮", "Развлечения"),
    ("housing", "🏠", "Жильё"),
    ("education", "📚", "Учёба"),
    ("health", "💊", "Здоровье"),
    ("clothes", "👕", "Одежда"),
    ("communication", "📱", "Связь"),
    ("other", "✨", "Другое"),
)

# Максимальная длина лога
MAX_LOG_LEN = 400