import os
import django
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_dashboard.settings')
django.setup()

from telegram_bot.handlers import setup_bot_application

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    print("Starting Telegram bot...")
    try:
        application = setup_bot_application()
        print("Bot is running. Press Ctrl+C to stop.")
        application.run_polling()
    except Exception as e:
        print(f"Bot error: {e}")