"""Клавиатуры бота"""
from telebot import types
from config import EXPENSE_CATEGORIES


# Главное меню
MAIN_MENU_LAYOUT = (
    ("➕ Расход", "💰 Доход"),
    ("📊 Сегодня", "📈 Неделя", "🗓️ Месяц"),
    ("📰 История", "🎯 Бюджеты"),
)


def build_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in MAIN_MENU_LAYOUT:
        markup.row(*(types.KeyboardButton(btn) for btn in row))
    return markup


def build_categories_keyboard(action: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for key, emoji, title in EXPENSE_CATEGORIES:
        buttons.append(types.InlineKeyboardButton(
            text=f"{emoji} {title}", 
            callback_data=f"{action}:{key}"
        ))
    
    while buttons:
        row = buttons[:3]
        buttons = buttons[3:]
        markup.row(*row)
    return markup


def build_comment_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text="Пропустить 💨", 
        callback_data="skip_comment"
    ))
    return markup


# Константа для callback
SKIP_COMMENT_CALLBACK = "skip_comment"