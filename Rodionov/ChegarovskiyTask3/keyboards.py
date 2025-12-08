"""Клавиатуры для бота"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import EMOJI

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура меню"""
    keyboard = [
        [f"{EMOJI['slot']} Слоты", f"{EMOJI['dice']} Кости"],
        [f"{EMOJI['cards']} Блекджек", f"{EMOJI['roulette']} Рулетка"],
        [f"{EMOJI['money']} Баланс", f"{EMOJI['trophy']} Топ игроков"],
        [f"{EMOJI['bonus']} Бонус"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Назад'"""
    keyboard = [[InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)

def get_dice_bet_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ставок в костях"""
    keyboard = [
        [
            InlineKeyboardButton("Чёт", callback_data="dice_even"),
            InlineKeyboardButton("Нечёт", callback_data="dice_odd")
        ],
        [
            InlineKeyboardButton("Конкретное число", callback_data="dice_number"),
            InlineKeyboardButton("Дубль", callback_data="dice_double")
        ],
        [InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_blackjack_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для блекджека"""
    keyboard = [
        [
            InlineKeyboardButton("Взять карту", callback_data="bj_hit"),
            InlineKeyboardButton("Остановиться", callback_data="bj_stand")
        ],
        [InlineKeyboardButton(f"{EMOJI['back']} Выйти", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_roulette_bet_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ставок в рулетке"""
    keyboard = [
        [
            InlineKeyboardButton("Число", callback_data="roulette_number"),
            InlineKeyboardButton("Цвет", callback_data="roulette_color")
        ],
        [
            InlineKeyboardButton("Чёт/Нечёт", callback_data="roulette_even_odd"),
        ],
        [InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_roulette_color_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора цвета в рулетке"""
    keyboard = [
        [
            InlineKeyboardButton("🔴 Красное", callback_data="color_red"),
            InlineKeyboardButton("⚫ Чёрное", callback_data="color_black")
        ],
        [InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_roulette_even_odd_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для чёт/нечёт в рулетке"""
    keyboard = [
        [
            InlineKeyboardButton("🔢 Чёт", callback_data="even_odd_even"),
            InlineKeyboardButton("🔣 Нечёт", callback_data="even_odd_odd")
        ],
        [InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)