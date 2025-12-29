"""
Класс для валидации пользовательского ввода
Используется во всех обработчиках для единообразной проверки
"""
import logging
from telegram import Update

logger = logging.getLogger(__name__)

class InputValidator:
    """Класс для проверки и валидации пользовательского ввода"""
    
    def __init__(self):
        self.validation_rules = {
            "dice_number": {"min": 2, "max": 12, "message": "❌ Число должно быть от 2 до 12!"},
            "roulette_number": {"min": 0, "max": 36, "message": "❌ Число должно быть от 0 до 36!"},
            "bet_amount": {"min": 1, "message": "❌ Ставка должна быть положительным числом!"}
        }
    
    async def validate_and_convert(self, update: Update, text: str, field_name: str = "число") -> tuple[int | None, str | None]:
        """Проверить и преобразовать ввод, вернуть (значение, ошибка)"""
        try:
            value = int(text)
            return value, None
        except ValueError as e:
            error_msg = f"❌ Введите целое {field_name}!"
            logger.warning(f"Ошибка преобразования числа: {text}, ошибка: {e}")
            await update.message.reply_text(error_msg)
            return None, error_msg
    
    async def validate_number_input(self, update: Update, text: str) -> int:
        """Проверить и преобразовать числовой ввод"""
        value, error = await self.validate_and_convert(update, text, "число")
        if error:
            raise ValueError(error)
        return value
    
    async def validate_bet_amount(self, update: Update, user_balance: int, bet_amount: int) -> bool:
        """Проверить валидность ставки"""
        if bet_amount <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительным числом!")
            return False
        
        if bet_amount > user_balance:
            await update.message.reply_text("❌ Недостаточно средств на балансе!")
            return False
        
        return True

    
    async def validate_game_input(self, update: Update, input_type: str, value: int) -> bool:
        """Универсальная проверка игрового ввода"""
        if input_type not in self.validation_rules:
            return True
        
        rule = self.validation_rules[input_type]
        
        if "min" in rule and value < rule["min"]:
            await update.message.reply_text(rule["message"])
            return False
        
        if "max" in rule and value > rule["max"]:
            await update.message.reply_text(rule["message"])
            return False
        
        return True
