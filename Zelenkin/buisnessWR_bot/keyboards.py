from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CATEGORIES, INCOME_CATEGORIES


def get_categories_keyboard():
    """Клавиатура для выбора категорий расходов"""
    keyboard = []
    categories_list = list(CATEGORIES.items())

    # Создаем кнопки по 2 в ряд для компактности
    for i in range(0, len(categories_list), 2):
        row = []
        for j in range(2):
            if i + j < len(categories_list):
                key, value = categories_list[i + j]
                row.append(InlineKeyboardButton(value, callback_data=f"category_{key}"))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def get_income_categories_keyboard():
    """Клавиатура для выбора категорий доходов"""
    keyboard = []
    categories_list = list(INCOME_CATEGORIES.items())

    for i in range(0, len(categories_list), 2):
        row = []
        for j in range(2):
            if i + j < len(categories_list):
                key, value = categories_list[i + j]
                row.append(InlineKeyboardButton(value, callback_data=f"income_{key}"))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def get_delete_keyboard(expense_id: int):
    """Клавиатура для удаления транзакции"""
    keyboard = [
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{expense_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    """Основное меню бота"""
    keyboard = [
        [InlineKeyboardButton("💸 Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton("💰 Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("📝 История", callback_data="history")],
        [InlineKeyboardButton("🎯 Бюджеты", callback_data="budgets")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_stats_keyboard():
    """Клавиатура для статистики"""
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="stats_today")],
        [InlineKeyboardButton("📆 Неделя", callback_data="stats_week")],
        [InlineKeyboardButton("📊 Месяц", callback_data="stats_month")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categories_keyboard():
    """Клавиатура для выбора категорий расходов"""
    keyboard = []
    categories_list = list(CATEGORIES.items())

    # Создаем кнопки по 2 в ряд для компактности
    for i in range(0, len(categories_list), 2):
        row = []
        for j in range(2):
            if i + j < len(categories_list):
                key, value = categories_list[i + j]
                row.append(InlineKeyboardButton(value, callback_data=f"category_{key}"))
        keyboard.append(row)

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(keyboard)


def get_income_categories_keyboard():
    """Клавиатура для выбора категорий доходов"""
    keyboard = []
    categories_list = list(INCOME_CATEGORIES.items())

    for i in range(0, len(categories_list), 2):
        row = []
        for j in range(2):
            if i + j < len(categories_list):
                key, value = categories_list[i + j]
                row.append(InlineKeyboardButton(value, callback_data=f"income_{key}"))
        keyboard.append(row)

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(keyboard)