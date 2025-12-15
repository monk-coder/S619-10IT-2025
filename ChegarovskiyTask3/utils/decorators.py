"""
Декораторы для валидации и проверок
"""
import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from utils.validator import InputValidator

logger = logging.getLogger(__name__)
db = Database()
validator = InputValidator()

def require_user(func):
    """Декоратор для проверки существования пользователя"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ Сначала используйте /start")
            return
        
        return await func(update, context, user_data, *args, **kwargs)
    
    return wrapper

def validate_bet(func):
    """Декоратор для проверки ставки"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ Сначала используйте /start")
            return
        
        try:
            bet_amount = int(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ Введите целое число!")
            return
        
        if not await validator.validate_bet_amount(update, user_data['balance'], bet_amount):
            return
        
        kwargs['user_data'] = user_data
        kwargs['bet_amount'] = bet_amount
        return await func(update, context, *args, **kwargs)
    
    return wrapper
