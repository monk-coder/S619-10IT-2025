from telegram import Update
from telegram.ext import ContextTypes
from bot.database.operations import DatabaseManager
from bot.games.coin_flip import CoinFlipGame
from bot.config import Config


async def coin_flip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    # Проверка аргументов
    if len(context.args) < 2:
        await message.reply_text("❌ Использование: /coin <орёл/решка> <ставка>")
        return

    choice = context.args[0]

    try:
        bet = int(context.args[1])
    except ValueError:
        await message.reply_text("❌ Ставка должна быть числом!")
        return

    # Инициализация
    config = Config()
    db_manager = DatabaseManager("sqlite:///data/database.db")
    session = db_manager.Session()

    # Запуск игры
    game = CoinFlipGame(config.GAMES['coin_flip'], session)
    result = await game.play(user.id, bet, choice)

    # Форматирование результата
    if result.success:
        result_text = f"🪙 Монетка: {result.details['result'].upper()}"
        response = f"""
{result_text}

{result.message}
💰 Баланс изменен на: {f"+{result.amount}" if result.win else result.amount} монет
        """
    else:
        response = result.message

    await message.reply_text(response)
    session.close()