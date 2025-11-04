from telegram import Update
from telegram.ext import ContextTypes
from bot.database.operations import DatabaseManager, UserOperations


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    db_manager = DatabaseManager("sqlite:///data/database.db")
    session = db_manager.Session()
    user_ops = UserOperations(session)

    user_data = await user_ops.get_user(user.id)

    if user_data:
        balance_text = f"""
💰 Ваш баланс: {user_data.balance:.0f} монет

📊 Статистика:
• Сыграно игр: {user_data.games_played}
• Общий выигрыш: {user_data.total_winnings:.0f} монет
• Всего поставлено: {user_data.total_bets:.0f} монет
        """
    else:
        balance_text = "❌ Пользователь не найден. Используйте /start"

    await update.message.reply_text(balance_text)
    session.close()