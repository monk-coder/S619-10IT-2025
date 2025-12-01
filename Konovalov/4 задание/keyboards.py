from telebot import types
from config import CATEGORIES

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("➕ Расход", "💰 Доход")
    keyboard.add("📊 Сегодня", "📈 Неделя")
    keyboard.add("📰 История", "🎯 Бюджеты")
    return keyboard

def categories_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for cat_id, (emoji, name) in CATEGORIES.items():
        buttons.append(
            types.InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"cat_{cat_id}"
            )
        )
    
    # Распределяем по 2 в ряд
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.add(*row)
    
    return keyboard