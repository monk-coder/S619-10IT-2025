# keyboards/game_keyboards.py
from telebot import types

def get_bet_keyboard(game_type: str):
    """Клавиатура выбора ставки"""
    markup = types.InlineKeyboardMarkup(row_width=3)

    bets = [10, 50, 100, 200, 500]
    buttons = []

    for bet in bets:
        buttons.append(types.InlineKeyboardButton(
            f'{bet} 🪙',
            callback_data=f'bet_{game_type}_{bet}'
        ))

    buttons.append(types.InlineKeyboardButton(
        '💎 Своя ставка',
        callback_data=f'bet_{game_type}_custom'
    ))

    buttons.append(types.InlineKeyboardButton(
        '🔙 Назад',
        callback_data='back_to_games'
    ))

    # Добавляем кнопки в 3 колонки
    for i in range(0, len(buttons) - 2, 3):
        markup.add(*buttons[i:i + 3])

    markup.add(buttons[-2], buttons[-1])
    return markup

def get_roulette_bet_keyboard():
    """Клавиатура для ставок в рулетке"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Ставки на цвет
    markup.row(
        types.InlineKeyboardButton('🔴 Красное', callback_data='roulette_color_red'),
        types.InlineKeyboardButton('⚫ Чёрное', callback_data='roulette_color_black')
    )

    markup.row(
        types.InlineKeyboardButton('🟢 Зелёное (0)', callback_data='roulette_color_green'),
        types.InlineKeyboardButton('🎯 Конкретное число', callback_data='roulette_specific')
    )

    # Ставки на четность
    markup.row(
        types.InlineKeyboardButton('🔢 Чётное', callback_data='roulette_even_odd_even'),
        types.InlineKeyboardButton('🔣 Нечётное', callback_data='roulette_even_odd_odd')
    )

    # Ставки на дюжины
    markup.row(
        types.InlineKeyboardButton('1-12', callback_data='roulette_dozen_1'),
        types.InlineKeyboardButton('13-24', callback_data='roulette_dozen_2'),
        types.InlineKeyboardButton('25-36', callback_data='roulette_dozen_3')
    )

    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_games'))

    return markup

def get_quick_bet_keyboard(game_type: str):
    """Быстрая клавиатура для повторной игры"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton('🎮 Играть ещё', callback_data=f'quick_play_{game_type}'),
        types.InlineKeyboardButton('💰 Изменить ставку', callback_data=f'change_bet_{game_type}'),
        types.InlineKeyboardButton('🔙 В меню', callback_data='back_to_menu')
    ]

    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2])
    return markup