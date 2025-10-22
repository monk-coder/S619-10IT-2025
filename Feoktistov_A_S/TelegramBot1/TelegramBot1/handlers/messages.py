from telegram import Update
from telegram.ext import ContextTypes


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == 'помощь':
        await update.message.reply_text("Чем могу помочь?")
    elif text == 'информация':
        await update.message.reply_text("Информация о проекте")
    else:
        await update.message.reply_text(f"Вы написали: {update.message.text}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Классное фото! 📸")