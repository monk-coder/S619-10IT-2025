"""
Главный модуль запуска Telegram бота казино
Оркестратор всего приложения, регистрирует обработчики и запускает бота
"""
import logging
import ssl
import certifi
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN

# Создаем кастомный SSL контекст с правильными сертификатами
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Настройка логирования для отслеживания работы приложения
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_application():
    """
    Фабрика для создания приложения Telegram бота
    Возвращает сконфигурированный экземпляр Application
    """
    return Application.builder().token(BOT_TOKEN).build()

def register_handlers(application: Application):
    """
    Регистрация всех обработчиков сообщений и callback-запросов
    Разделяет обработчики по типам для лучшей читаемости
    """
    # Импорты внутри функции для избежания циклических зависимостей
    from handlers.commands import start, show_balance, show_top_players, get_bonus
    from handlers.games_handler import start_slots, start_dice, start_blackjack, start_roulette
    from handlers.bet_handler import handle_bet
    from handlers.callback_handler import handle_callback_query

    # Обработчики текстовых команд (главное меню)
    command_handlers = [
        CommandHandler("start", start),
        CommandHandler("bonus", get_bonus),
        MessageHandler(filters.Regex("^💰 Баланс$"), show_balance),
        MessageHandler(filters.Regex("^🏆 Топ игроков$"), show_top_players),
        MessageHandler(filters.Regex("^🎁 Бонус$"), get_bonus),
    ]

    # Обработчики запуска игр
    game_handlers = [
        MessageHandler(filters.Regex("^🎰 Слоты$"), start_slots),
        MessageHandler(filters.Regex("^🎲 Кости$"), start_dice),
        MessageHandler(filters.Regex("^🃏 Блекджек$"), start_blackjack),
        MessageHandler(filters.Regex("^🎡 Рулетка$"), start_roulette),
    ]

    # Основные обработчики сообщений
    message_handlers = [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bet),
        CallbackQueryHandler(handle_callback_query),
    ]

    # Регистрация всех обработчиков в приложении
    all_handlers = command_handlers + game_handlers + message_handlers
    for handler in all_handlers:
        application.add_handler(handler)

def main():
    """
    Точка входа в приложение
    Инициализирует и запускает бота в режиме polling
    """
    try:
        application = create_application()
        register_handlers(application)

        logger.info("Бот инициализирован и готов к работе")
        application.run_polling(
            drop_pending_updates=True,  # Игнорируем сообщения, отправленные когда бот был оффлайн
            allowed_updates=['message', 'callback_query']  # Обрабатываем только нужные типы updates
        )

    except Exception as error:
        logger.error(f"Критическая ошибка при запуске: {error}")
        raise

if __name__ == "__main__":
    main()