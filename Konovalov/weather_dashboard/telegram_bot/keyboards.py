from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Основная клавиатура меню"""
    keyboard = [
        [KeyboardButton("🌤️ Погода сейчас"), KeyboardButton("⭐ Избранные города")],
        [KeyboardButton("📝 Мои задачи"), KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    keyboard = [[KeyboardButton("🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_favorite_cities_keyboard(cities):
    """Клавиатура с избранными городами"""
    keyboard = []
    for city in cities:
        keyboard.append([KeyboardButton(city)])
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_yes_no_keyboard():
    """Клавиатура Да/Нет"""
    keyboard = [
        [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)