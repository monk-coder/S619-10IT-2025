from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import db


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id)

    keyboard = [
        ['🎰 Слоты', ],
        ['🎲 Кости', '🃏 Блекджек'],
        ['💰 Баланс', '📊 Статистика']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"🎉 Добро пожаловать в Казино, {user.first_name}!\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n\n"
        "Выберите игру:",
        reply_markup=reply_markup
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)

    await update.message.reply_text(
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"🎮 Игр сыграно: {user_data['games_played']}\n"
        f"🏆 Побед: {user_data['wins']}"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    win_rate = (user_data['wins'] / user_data['games_played'] * 100) if user_data['games_played'] > 0 else 0

    await update.message.reply_text(
        f"📊 Ваша статистика:\n"
        f"💰 Баланс: {user_data['balance']} монет\n"
        f"🎮 Всего игр: {user_data['games_played']}\n"
        f"🏆 Побед: {user_data['wins']}\n"
        f"📈 Винрейт: {win_rate:.1f}%"
    )