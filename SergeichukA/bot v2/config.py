import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8592210277:AAFa0JTsmU9pYxq_1dScgNpmDsZSduA9aLw")
DB_PATH = os.getenv("SECRET_SANTA_DB", "secret_santa.sqlite3")

# Константы кнопок
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