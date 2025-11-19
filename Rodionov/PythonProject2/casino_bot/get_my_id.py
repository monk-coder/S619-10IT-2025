# get_my_id.py - запустите этот файл отдельно чтобы узнать ваш ID
import os
import sys
from dotenv import load_dotenv

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

import telebot
from config.config import Config

# Получение токена бота
BOT_TOKEN = os.getenv('BOT_TOKEN') or Config.BOT_TOKEN

if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("❌ BOT_TOKEN не найден в .env файле")
    print("📝 Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен_бота")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'id', 'myid'])
def send_id(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    response = f"""
👤 *Ваши данные:*

🆔 *ID:* `{user_id}`
👤 *Имя:* {first_name}
📛 *Username:* @{username or 'не установлен'}

📋 *Для добавления в админы:*
В файле `config/config.py` замените:
`ADMIN_IDS = [123456789]` 
на
`ADMIN_IDS = [{user_id}]`

💡 *После изменения перезапустите бота!*
    """

    bot.send_message(message.chat.id, response, parse_mode='Markdown')
    print(f"✅ ID пользователя {first_name}: {user_id}")


print("🤖 Бот для получения ID запущен...")
print("📨 Отправьте боту команду /id или /myid чтобы узнать ваш ID")
print("🛑 Для остановки нажмите Ctrl+C")

try:
    bot.infinity_polling()
except KeyboardInterrupt:
    print("\n🛑 Бот остановлен")