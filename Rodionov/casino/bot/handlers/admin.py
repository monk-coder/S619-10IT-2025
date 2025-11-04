from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    config = Config()

    if user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    admin_text = """
👑 Панель администратора

Доступные команды:
• /admin stats - статистика бота
• /admin users - управление пользователями
• /admin broadcast - рассылка сообщений
    """

    await update.message.reply_text(admin_text)