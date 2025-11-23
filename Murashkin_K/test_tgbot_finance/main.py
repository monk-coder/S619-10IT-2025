import telebot
from config import TOKEN
from handlers import register_handlers

bot = telebot.TeleBot(TOKEN)

register_handlers(bot)

bot.infinity_polling()
