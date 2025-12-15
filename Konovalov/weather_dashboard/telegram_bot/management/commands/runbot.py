from django.core.management.base import BaseCommand
from telegram_bot.handlers import setup_bot_application
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the Telegram bot'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Telegram bot...')
        )
        
        try:
            application = setup_bot_application()
            
            self.stdout.write(
                self.style.SUCCESS('Bot is running. Press Ctrl+C to stop.')
            )
            
            # Запускаем бота
            application.run_polling()
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.stdout.write(
                self.style.ERROR(f'Bot error: {e}')
            )