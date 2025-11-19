import telebot
from config import BOT_TOKEN

# Создаем единственный экземпляр бота
try:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    print("✅ Бот инициализирован успешно")
except Exception as e:
    print(f"❌ Ошибка инициализации бота: {e}")
    raise
