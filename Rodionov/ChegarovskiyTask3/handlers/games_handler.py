"""Обработчики запуска игр"""
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from keyboards import get_back_keyboard, get_dice_bet_keyboard, get_roulette_bet_keyboard

db = Database()

async def start_slots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в слоты"""
    await update.message.reply_text(
        "🎰 **ИГРА: СЛОТ-МАШИНА**\n\n"
        "Введите сумму ставки (целое число):",
        reply_markup=get_back_keyboard()
    )
    context.user_data["current_game"] = "slots"

async def start_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в кости"""
    await update.message.reply_text(
        "🎲 **ИГРА: КОСТИ**\n\n"
        "Выберите тип ставки:",
        reply_markup=get_dice_bet_keyboard()
    )
    context.user_data["current_game"] = "dice"

async def start_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в блекджек"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return

    await update.message.reply_text(
        "🃏 **ИГРА: БЛЕКДЖЕК**\n\n"
        "Введите сумму ставки (целое число):",
        reply_markup=get_back_keyboard()
    )
    context.user_data["current_game"] = "blackjack"

async def start_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в рулетку"""
    await update.message.reply_text(
        "🎡 **ИГРА: РУЛЕТКА**\n\n"
        "Выберите тип ставки:",
        reply_markup=get_roulette_bet_keyboard()
    )
    context.user_data["current_game"] = "roulette"