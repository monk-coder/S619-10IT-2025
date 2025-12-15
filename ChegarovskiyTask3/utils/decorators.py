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
        
        kwargs['user_data'] = user_data
        return await func(update, context, *args, **kwargs)
    
    return wrapper
