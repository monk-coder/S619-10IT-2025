from telegram import Update
from telegram.ext import ContextTypes
from bot.database.operations import DatabaseManager
from bot.games.slots import SlotsGame
from bot.config import Config


async def slots_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    # Получение ставки из аргументов
    if not context.args:
        await message.reply_text("❌ Укажите ставку: /slots <ставка>")
        return

    try:
        bet = int(context.args[0])
    except ValueError:
        await message.reply_text("❌ Ставка должна быть числом!")
        return

    # Инициализация
    config = Config()
    db_manager = DatabaseManager("sqlite:///data/database.db")
    session = db_manager.Session()

    # Запуск игры
    game = SlotsGame(config.GAMES['slots'], session)
    result = await game.play(user.id, bet)

    # Форматирование результата
    if result.success:
        reels_display = " | ".join(result.details['reels'])
        response = f"""
🎰 СЛОТЫ 🎰

{reels_display}

{result.message}
💰 Баланс изменен на: {f"+{result.amount}" if result.win else result.amount} монет
        """
    else:
        response = result.message

    await message.reply_text(response)
    session.close()