import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import Application
from bot.config import Config
from bot.handlers import setup_handlers
from bot.database.operations import DatabaseManager

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('data/logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


async def main():
    # Проверка токена
    if not os.getenv("BOT_TOKEN"):
        logging.error("BOT_TOKEN не найден в переменных окружения")
        return

    # Инициализация конфига
    config = Config()

    # Инициализация базы данных
    db_manager = DatabaseManager(config.DATABASE_URL)
    logging.info("База данных инициализирована")

    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Настройка обработчиков
    setup_handlers(application)

    # Запуск бота
    logging.info("Бот запущен...")
    await application.run_polling()


if __name__ == "__main__":
    # Создание необходимых директорий
    os.makedirs('data/logs', exist_ok=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")