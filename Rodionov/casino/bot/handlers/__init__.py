from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers.start import start_handler
from bot.handlers.balance import balance_handler
from bot.handlers.games.slots import slots_handler
from bot.handlers.games.coin_flip import coin_flip_handler
from bot.handlers.admin import admin_handler
from bot.handlers.callbacks import callback_handler


def setup_handlers(application: Application):
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("balance", balance_handler))
    application.add_handler(CommandHandler("slots", slots_handler))
    application.add_handler(CommandHandler("coin", coin_flip_handler))
    application.add_handler(CommandHandler("admin", admin_handler))

    # Callback кнопки
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Сообщения
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))