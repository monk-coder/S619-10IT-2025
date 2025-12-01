import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    exit("Ошибка: TELEGRAM_BOT_TOKEN не установлен")

DB_PATH = os.getenv("FINANCE_TRACKER_DB", "finance_tracker.sqlite3")

CATEGORIES = {
    "food": ("🍔", "Еда"),
    "transport": ("🚌", "Транспорт"),
    "entertainment": ("🎮", "Развлечения"),
    "housing": ("🏠", "Жильё"),
    "education": ("📚", "Учёба"),
    "health": ("💊", "Здоровье"),
    "clothes": ("👕", "Одежда"),
    "communication": ("📱", "Связь"),
    "other": ("✨", "Другое"),
}