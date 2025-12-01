from telebot import types
from config import EXPENSE_CATEGORIES

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Расход", "💰 Доход")
    markup.row("📊 Сегодня", "📈 Неделя", "🗓️ Месяц")
    markup.row("📰 История", "🎯 Бюджеты")
    return markup

def categories_menu(action="add"):
    markup = types.InlineKeyboardMarkup(row_width=3)
    for cat in EXPENSE_CATEGORIES:
        markup.add(types.InlineKeyboardButton(
            f"{cat[1]} {cat[2]}", 
            callback_data=f"{action}:{cat[0]}"
        ))
    return markup

def skip_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Пропустить 💨", callback_data="skip"))
    return markup