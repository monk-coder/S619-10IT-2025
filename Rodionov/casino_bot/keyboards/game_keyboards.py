# keyboards/game_keyboards.py
from telebot import types
from config.config import Config


def get_bet_keyboard(game_type: str):
    """Клавиатура выбора ставки"""
    markup = types.InlineKeyboardMarkup(row_width=3)

    buttons = [
        types.InlineKeyboardButton('10 🪙', callback_data=f'bet_{game_type}_10'),
        types.InlineKeyboardButton('50 🪙', callback_data=f'bet_{game_type}_50'),
        types.InlineKeyboardButton('100 🪙', callback_data=f'bet_{game_type}_100'),
        types.InlineKeyboardButton('500 🪙', callback_data=f'bet_{game_type}_500'),
        types.InlineKeyboardButton('1000 🪙', callback_data=f'bet_{game_type}_1000'),
        types.InlineKeyboardButton('⚙️ Своя ставка', callback_data=f'bet_{game_type}_custom')
    ]

    markup.add(buttons[0], buttons[1], buttons[2])
    markup.add(buttons[3], buttons[4], buttons[5])
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_menu'))

    return markup


def get_quick_bet_keyboard(game_type: str):
    """Клавиатура быстрой повторной игры"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton('🔄 Играть снова', callback_data=f'quick_play_{game_type}'),
        types.InlineKeyboardButton('⚙️ Изменить ставку', callback_data=f'change_bet_{game_type}'),
        types.InlineKeyboardButton('🔙 В меню', callback_data='back_to_menu')
    ]

    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2])

    return markup


def get_roulette_bet_keyboard():
    """Клавиатура выбора типа ставки в рулетке"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton('🔴 Красное', callback_data='roulette_color_red'),
        types.InlineKeyboardButton('⚫ Чёрное', callback_data='roulette_color_black'),
        types.InlineKeyboardButton('🟢 Зелёное (0)', callback_data='roulette_color_green'),
        types.InlineKeyboardButton('🔢 Чётное', callback_data='roulette_even_odd_even'),
        types.InlineKeyboardButton('🔢 Нечётное', callback_data='roulette_even_odd_odd'),
        types.InlineKeyboardButton('🎯 Конкретное число', callback_data='roulette_specific'),
        types.InlineKeyboardButton('1-12', callback_data='roulette_dozen_1'),
        types.InlineKeyboardButton('13-24', callback_data='roulette_dozen_2'),
        types.InlineKeyboardButton('25-36', callback_data='roulette_dozen_3')
    ]

    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2])
    markup.add(buttons[3], buttons[4])
    markup.add(buttons[5])
    markup.add(buttons[6], buttons[7], buttons[8])
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_games'))

    return markup


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_to_menu'))
    return markup