"""Конфигурация бота."""
import os
import logging

# Настройки бота
BOT_TOKEN = "8365732213:AAGSdfr0dBluuihxiG1wLakIaWyGw3LsCkQ"
if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
    logging.warning("Set TELEGRAM_BOT_TOKEN before running the bot.")

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