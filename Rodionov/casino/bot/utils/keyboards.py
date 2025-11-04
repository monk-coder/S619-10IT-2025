from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎰 Слоты", callback_data="game_slots"),
            InlineKeyboardButton("🪙 Монетка", callback_data="game_coin")
        ],
        [
            InlineKeyboardButton("🎡 Рулетка", callback_data="game_roulette"),
            InlineKeyboardButton("🎯 Кости", callback_data="game_dice")
        ],
        [
            InlineKeyboardButton("💰 Баланс", callback_data="balance"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🎁 Бонус", callback_data="daily_bonus"),
            InlineKeyboardButton("🏆 Лидеры", callback_data="leaders")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def slots_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎰 Играть (10)", callback_data="slots_play_10"),
            InlineKeyboardButton("🎰 Играть (50)", callback_data="slots_play_50")
        ],
        [
            InlineKeyboardButton("🎰 Играть (100)", callback_data="slots_play_100"),
            InlineKeyboardButton("🎰 Своя ставка", callback_data="slots_custom")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def coin_flip_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🦅 Орёл", callback_data="coin_орёл"),
            InlineKeyboardButton("🪙 Решка", callback_data="coin_решка")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)