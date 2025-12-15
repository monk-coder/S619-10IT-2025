import logging
from telebot import types
from bot_instance import bot
from database import ensure_schema
from handlers.basic_handlers import setup_basic_handlers
from handlers.profile_handlers import setup_profile_handlers
from handlers.wishlist_handlers import setup_wishlist_handlers
from handlers.game_handlers import setup_game_handlers
from handlers.step_handlers import setup_step_handlers

def setup_bot_commands():
    """Настройка команд бота"""
    bot.set_my_commands([
        types.BotCommand("start", "Запустить бота 🎅"),
        types.BotCommand("help", "Список возможностей 📖"),
        types.BotCommand("menu", "Главное меню 🏠"),
        types.BotCommand("profile", "Показать профиль 👤"),
        types.BotCommand("edit_profile", "Обновить профиль ✏️"),
        types.BotCommand("wishlist", "Мой вишлист 🎁"),
        types.BotCommand("add_item", "Добавить подарок ➕"),
        types.BotCommand("create_game", "Создать игру 🎲"),
        types.BotCommand("status", "Игры, где я организатор 🔔"),
        types.BotCommand("my_recipient", "Мой получатель 🎁"),
    ])

def setup_all_handlers():
    """Настройка всех обработчиков"""
    setup_basic_handlers()
    setup_profile_handlers()
    setup_wishlist_handlers()
    setup_game_handlers()
    setup_step_handlers()

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s"
    )
    
    # Инициализация базы данных
    ensure_schema()
    
    # Настройка команд и обработчиков
    setup_bot_commands()
    setup_all_handlers()
    
    # Запуск бота
    print("Бот запускается...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    main()