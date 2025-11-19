"""Конфигурация бота."""
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN не найден в .env файле!")
    logging.error("📝 Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен")
    exit(1)

if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE" or BOT_TOKEN == "8365732213:AAGSdfr0dBluuihxiG1wLakIaWyGw3LsCkQ":
    logging.warning("⚠️  Замените BOT_TOKEN в .env файле на ваш настоящий токен!")

# Настройки базы данных
DB_PATH = os.environ.get(
    "SECRET_SANTA_DB",
    os.path.join(os.path.dirname(__file__), "secret_santa.sqlite3"),
)

# Настройки логирования
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Константы кнопок
BTN_PROFILE = "👤 Мой профиль"
BTN_EDIT_PROFILE = "✏️ Редактировать профиль"
BTN_WISHLIST = "🎁 Мой вишлист"
BTN_ADD_WISH = "➕ Добавить желание"
BTN_REMOVE_WISH = "🗑️ Удалить желание"
BTN_CREATE_GAME = "🎄 Создать игру"
BTN_MY_GAMES = "📋 Мои игры"
BTN_JOIN_GAME = "🎮 Присоединиться"
BTN_LEAVE_GAME = "🚪 Покинуть игру"
BTN_PARTICIPANTS = "👥 Участники"
BTN_DRAW = "🎉 Провести жеребьёвку"
BTN_MY_RECIPIENT = "🎯 Кому я дарю?"
BTN_MAIN_MENU = "🏠 Главное меню"
BTN_ASK_SANTA = "❓ Задать вопрос"