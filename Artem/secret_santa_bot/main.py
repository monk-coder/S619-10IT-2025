"""Главный файл запуска бота."""
import logging

from database.operations import ensure_schema
from bot.bot import bot, setup_bot_commands
from config import LOG_FORMAT, LOG_DATE_FORMAT

# Импорты обработчиков (важно для регистрации)
from bot.handlers import base, profile, wishlist, games, commands


def main() -> None:
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO, 
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
    logger = logging.getLogger("secret_santa_bot")
    
    # Инициализация базы данных
    ensure_schema()
    
    # Настройка команд бота
    setup_bot_commands()
    
    logger.info("🚀 Бот Тайный Санта запущен!")
    
    # Запуск бота
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()