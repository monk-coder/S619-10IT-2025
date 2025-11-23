import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = 'finance_bot.db'

# Категории расходов
CATEGORIES = {
    'food': '🍔 Еда',
    'transport': '🚌 Транспорт',
    'entertainment': '🎮 Развлечения',
    'housing': '🏠 Жильё',
    'education': '📚 Учёба',
    'health': '💊 Здоровье',
    'clothes': '👕 Одежда',
    'communication': '📱 Связь',
    'other': '✨ Другое'
}

# Категории доходов
INCOME_CATEGORIES = {
    'pocket_money': '💵 Карманные деньги',
    'part_time': '💼 Подработка',
    'scholarship': '🎓 Стипендия',
    'salary': '💰 Зарплата',
    'other_income': '✨ Другое'
}