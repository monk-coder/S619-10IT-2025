"""Инициализация бота и меню."""
import telebot
from telebot import types

from config import BOT_TOKEN, BTN_PROFILE, BTN_WISHLIST, BTN_CREATE_GAME, BTN_MY_GAMES
from config import BTN_JOIN_GAME, BTN_MY_RECIPIENT, BTN_ASK_SANTA, BTN_MAIN_MENU
from config import BTN_EDIT_PROFILE, BTN_ADD_WISH, BTN_REMOVE_WISH
from config import BTN_PARTICIPANTS, BTN_DRAW, BTN_LEAVE_GAME

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Установка команд бота
def setup_bot_commands():
    try:
        bot.set_my_commands([
            types.BotCommand("start", "Запустить бота 🎅"),
            types.BotCommand("help", "Помощь 📖"),
            types.BotCommand("menu", "Меню 🏠"),
            types.BotCommand("profile", "Профиль 👤"),
            types.BotCommand("wishlist", "Мой вишлист 🎁"),
            types.BotCommand("create", "Создать игру 🎲"),
            types.BotCommand("games", "Мои игры 🔔"),
            types.BotCommand("recipient", "Мой получатель 🎁"),
        ])
        print("✅ Команды бота установлены")
    except Exception as e:
        print(f"⚠️ Не удалось установить команды бота: {e}")
        print("ℹ️ Бот будет работать, но команды меню могут быть недоступны")

# Структуры меню (остальной код без изменений)
MAIN_MENU_LAYOUT = [
    [BTN_PROFILE, BTN_WISHLIST],
    [BTN_CREATE_GAME, BTN_MY_GAMES],
    [BTN_JOIN_GAME, BTN_MY_RECIPIENT],
    [BTN_ASK_SANTA, BTN_MAIN_MENU]
]

PROFILE_MENU_LAYOUT = [
    [BTN_EDIT_PROFILE, BTN_WISHLIST],
    [BTN_MAIN_MENU]
]

WISHLIST_MENU_LAYOUT = [
    [BTN_ADD_WISH, BTN_REMOVE_WISH],
    [BTN_MAIN_MENU]
]

GAME_MENU_LAYOUT = [
    [BTN_PARTICIPANTS, BTN_DRAW],
    [BTN_JOIN_GAME, BTN_LEAVE_GAME],
    [BTN_MAIN_MENU]
]

def build_menu(buttons_layout: list[list[str]]) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    for row in buttons_layout:
        markup.row(*(types.KeyboardButton(btn) for btn in row))
    return markup

def send_main_menu(chat_id: int, text: str = "🎅 Добро пожаловать в Тайного Санту! Выберите действие:"):
    bot.send_message(chat_id, text, reply_markup=build_menu(MAIN_MENU_LAYOUT))

def send_profile_menu(chat_id: int, text: str = "👤 Управление профилем:"):
    bot.send_message(chat_id, text, reply_markup=build_menu(PROFILE_MENU_LAYOUT))

def send_wishlist_menu(chat_id: int, text: str = "🎁 Управление вишлистом:"):
    bot.send_message(chat_id, text, reply_markup=build_menu(WISHLIST_MENU_LAYOUT))

def send_game_menu(chat_id: int, text: str = "🎮 Управление игрой:"):
    bot.send_message(chat_id, text, reply_markup=build_menu(GAME_MENU_LAYOUT))