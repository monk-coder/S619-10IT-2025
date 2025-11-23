from telebot import types
from config import CATEGORIES

def categories_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=name, callback_data=key) for key, name in CATEGORIES.items()]
    keyboard.add(*buttons)
    return keyboard
