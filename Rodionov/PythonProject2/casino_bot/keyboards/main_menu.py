# keyboards/main_menu.py
from telebot import types


def get_main_menu():
    """Главное меню с кнопкой ежедневного бонуса"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    buttons = [
        types.KeyboardButton('🎰 Слоты'),
        types.KeyboardButton('🎯 Кости'),
        types.KeyboardButton('🎡 Рулетка'),
        types.KeyboardButton('🎁 Ежедневный бонус'),
        types.KeyboardButton('💰 Баланс'),
        types.KeyboardButton('📊 Глобальная статистика'),
        types.KeyboardButton('🏆 Топ игроков'),
        types.KeyboardButton('👤 Профиль'),
        types.KeyboardButton('ℹ️ Помощь')
    ]

    # Распределяем кнопки по рядам
    markup.row(buttons[0], buttons[1], buttons[2])  # Игры
    markup.row(buttons[3])  # Бонус
    markup.row(buttons[4], buttons[5])  # Баланс и статистика
    markup.row(buttons[6], buttons[7])  # Топ и профиль
    markup.row(buttons[8])  # Помощь

    return markup


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 В меню', callback_data='back_to_menu'))
    return markup