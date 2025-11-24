# keyboards/main_menu.py
from telebot import types


def get_main_menu():
    """Главное меню бота"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    buttons = [
        types.KeyboardButton('🎰 Слоты'),
        types.KeyboardButton('🎯 Кости'),
        types.KeyboardButton('🎡 Рулетка'),
        types.KeyboardButton('💰 Баланс'),
        types.KeyboardButton('📊 Статистика'),
        types.KeyboardButton('🌍 Глобальная статистика'),
        types.KeyboardButton('🏆 Топ игроков'),
        types.KeyboardButton('👤 Профиль'),
        types.KeyboardButton('🎁 Ежедневный бонус'),
        types.KeyboardButton('ℹ️ Помощь')
    ]

    markup.add(buttons[0], buttons[1], buttons[2])
    markup.add(buttons[3], buttons[4], buttons[5])
    markup.add(buttons[6], buttons[7])
    markup.add(buttons[8], buttons[9])

    return markup


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔙 В главное меню'))
    return markup