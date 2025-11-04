from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.keyboards import main_menu_keyboard
from bot.database.operations import DatabaseManager, UserOperations


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    # Инициализация БД
    db_manager = DatabaseManager("sqlite:///data/database.db")
    session = db_manager.Session()
    user_ops = UserOperations(session)

    # Создание/получение пользователя
    await user_ops.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    welcome_text = f"""
🎰 Добро пожаловать в казино-бот, {user.first_name}!

💰 Ваш стартовый баланс: 1000 монет

🎮 Доступные игры:
• 🎰 Слоты - классические игровые автоматы
• 🪙 Монетка - угадай сторону
• 🎡 Рулетка - испытай удачу

💎 Особенности:
• Ежедневные бонусы
• Система достижений
• Таблица лидеров

Выберите игру из меню ниже и удачи! 🍀
    """

    keyboard = main_menu_keyboard()
    await message.reply_text(welcome_text, reply_markup=keyboard)

    session.close()