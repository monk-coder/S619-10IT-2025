# main.py
import logging
import os
import sys
import time
import signal
import threading
from dotenv import load_dotenv

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import telebot
from config.config import Config
from database.db_handler import DatabaseHandler
from handlers.main_handlers import MainHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.game_handlers import GameHandlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Глобальная переменная для контроля работы бота
bot_running = True
bot_instance = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global bot_running, bot_instance
    print(f"\n🛑 Получен сигнал {signum}. Остановка бота...")
    bot_running = False

    if bot_instance:
        try:
            logger.info("🛑 Останавливаем polling...")
            bot_instance.stop_polling()
        except Exception as e:
            logger.error(f"Ошибка при остановке polling: {e}")

def create_bot():
    """Создание бота"""
    try:
        # Загрузка переменных окружения
        load_dotenv()

        # Получение токена бота
        BOT_TOKEN = os.getenv('BOT_TOKEN') or Config.BOT_TOKEN

        if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ BOT_TOKEN не найден. Проверьте файл .env")
            print("❌ ОШИБКА: BOT_TOKEN не установлен!")
            print("📝 Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен_бота")
            return None

        logger.info("✅ Токен загружен")

        # Инициализация бота
        bot = telebot.TeleBot(
            BOT_TOKEN,
            parse_mode='Markdown',
            threaded=True,
            num_threads=4,
            skip_pending=True
        )

        # Тестируем соединение
        bot_info = bot.get_me()
        logger.info(f"✅ Бот успешно создан: @{bot_info.username}")
        return bot

    except Exception as e:
        logger.error(f"❌ Ошибка при создании бота: {e}")
        return None

def setup_bot_handlers(bot, db_handler):
    """Настройка обработчиков бота"""
    try:
        # Регистрация обработчиков в правильном порядке
        game_handlers = GameHandlers(bot, db_handler)
        admin_handlers = AdminHandlers(bot, db_handler)
        main_handlers = MainHandlers(bot, db_handler)

        # Сохраняем ссылку на game_handlers
        bot.game_handlers = game_handlers
        bot.admin_handlers = admin_handlers

        logger.info("✅ Все обработчики инициализированы")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке обработчиков: {e}")
        return False

def start_polling(bot):
    """Запуск polling в отдельном потоке"""

    def polling_thread():
        global bot_running
        while bot_running:
            try:
                logger.info("🔄 Запуск polling...")
                bot.infinity_polling(
                    timeout=20,
                    long_polling_timeout=10,
                    logger_level=logging.ERROR,
                    restart_on_change=False,
                    skip_pending=True
                )
            except Exception as e:
                if bot_running:
                    logger.error(f"❌ Ошибка в polling: {e}")
                    logger.info("🔄 Перезапуск polling через 5 секунд...")
                    time.sleep(5)
                else:
                    break

    thread = threading.Thread(target=polling_thread, daemon=True)
    thread.start()
    return thread

def main():
    """Основная функция запуска бота"""
    global bot_running, bot_instance

    print("🎰 Casino Bot запускается...")
    print("💡 Для остановки нажмите Ctrl+C")

    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Создаем бота
        bot = create_bot()
        if not bot:
            return

        bot_instance = bot  # Сохраняем глобальную ссылку

        # Инициализация базы данных
        db_handler = DatabaseHandler()

        # Настройка обработчиков
        if not setup_bot_handlers(bot, db_handler):
            logger.error("❌ Не удалось настроить обработчики")
            return

        # Обновляем статус бота в обработчиках
        if hasattr(bot, 'game_handlers'):
            bot.game_handlers.set_bot_running(True)
        if hasattr(bot, 'admin_handlers'):
            bot.admin_handlers.set_bot_running(True)

        logger.info("✅ Все компоненты инициализированы")
        print("✅ Бот запущен! Ожидаем сообщения...")
        print("👑 Для доступа к админ-панели используйте команду /admin")
        print("🛑 Для остановки нажмите Ctrl+C")

        # Запускаем polling в отдельном потоке
        polling_thread = start_polling(bot)

        # Главный цикл
        while bot_running and polling_thread.is_alive():
            time.sleep(1)

            if not polling_thread.is_alive() and bot_running:
                logger.warning("🔄 Polling thread умер, но бот еще должен работать")
                break

        print("👋 Завершаем работу бота...")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")

    finally:
        # Гарантируем остановку
        bot_running = False

        # Уведомляем обработчики о остановке
        if bot_instance:
            if hasattr(bot_instance, 'game_handlers'):
                bot_instance.game_handlers.set_bot_running(False)
            if hasattr(bot_instance, 'admin_handlers'):
                bot_instance.admin_handlers.set_bot_running(False)

        # Даем немного времени на завершение операций
        time.sleep(2)

        print("🧹 Очистка завершена")
        print("👋 Бот остановлен")

if __name__ == "__main__":
    main()