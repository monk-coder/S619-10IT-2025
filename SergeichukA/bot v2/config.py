import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверяем, что токен установлен
if not BOT_TOKEN:
    raise ValueError(
        "❌ Токен бота не найден! Создай файл .env с TELEGRAM_BOT_TOKEN\n"
        "📝 Пример: TELEGRAM_BOT_TOKEN=123456:ABCdef...\n"
        "🔧 Получи токен у @BotFather в Telegram"
    )

DB_PATH = os.getenv("SECRET_SANTA_DB", "secret_santa.sqlite3")

# Константы кнопок (остаются прежними)
BTN_PROFILE = "👤 Профиль"
BTN_EDIT_PROFILE = "✏️ Обновить профиль"
BTN_WISHLIST = "🎁 Мой вишлист"
BTN_ADD_ITEM = "➕ Добавить подарок"
BTN_REMOVE_ITEM = "❌ Удалить подарок"
BTN_CREATE_GAME = "🎲 Создать игру"
BTN_STATUS = "🔔 Мои игры"
BTN_JOIN_GAME = "🎮 Вступить в игру"
BTN_LEAVE_GAME = "🚪 Выйти из игры"
BTN_PARTICIPANTS = "👥 Участники игры"
BTN_MIX = "🎉 Провести жеребьёвку"
BTN_MY_RECIPIENT = "🎁 Кому дарю?"
BTN_MAIN_MENU = "🏠 Главное меню"

MENU_LAYOUT = [
    (BTN_PROFILE, BTN_EDIT_PROFILE),
    (BTN_WISHLIST, BTN_ADD_ITEM),
    (BTN_REMOVE_ITEM,),
    (BTN_CREATE_GAME, BTN_STATUS),
    (BTN_JOIN_GAME, BTN_LEAVE_GAME),
    (BTN_PARTICIPANTS, BTN_MIX),
    (BTN_MY_RECIPIENT, BTN_MAIN_MENU),
]


BUTTON_ACTIONS = {}
