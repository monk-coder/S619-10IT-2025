import asyncio
import threading
from bot import ClickerBot
from app import run_flask, auto_clicker_worker
import config
from database import db


def run_bot():
    bot = ClickerBot(config.Config.TOKEN)
    asyncio.run(bot.run())


def run_auto_clicker():
    auto_clicker_worker()


if __name__ == '__main__':
    # Инициализация базы данных
    db.init_db()

    # Запуск автокликера в отдельном потоке
    auto_clicker_thread = threading.Thread(target=run_auto_clicker, daemon=True)
    auto_clicker_thread.start()

    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Запуск Flask в основном потоке
    run_flask()
