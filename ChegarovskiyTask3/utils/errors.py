"""Утилиты для обработки ошибок"""
from telegram import Update
from telegram.ext import ContextTypes

async def validate_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, user_balance: int, bet_amount: int) -> bool:
    """Проверить валидность ставки"""
    if bet_amount <= 0:
        await update.message.reply_text("❌ Ставка должна быть положительным числом!")
        return False
    if bet_amount > user_balance:
        await update.message.reply_text("❌ Недостаточно средств на балансе!")
        return False
    return True

async def validate_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
    """Проверить и преобразовать числовой ввод"""
    try:
        return int(text)
    except ValueError:
        await update.message.reply_text("❌ Введите целое число!")
        return None