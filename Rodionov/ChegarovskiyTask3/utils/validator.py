"""
Класс для валидации пользовательского ввода
Используется во всех обработчиках для единообразной проверки
"""
from telegram import Update
from telegram.ext import ContextTypes

class InputValidator:
    """Класс для проверки и валидации пользовательского ввода"""
    
    @staticmethod
    async def validate_number_input(update: Update, text: str) -> int:
        """Проверить и преобразовать числовой ввод"""
        try:
            return int(text)
        except ValueError:
            await update.message.reply_text("❌ Введите целое число!")
            raise ValueError("Invalid number input")
    
    @staticmethod
    async def validate_bet_amount(update: Update, user_balance: int, bet_amount: int) -> bool:
        #Эта функция проверяет только ставку, но не проверяет результат игры (может ли баланс уйти в минус после вычитания проигрыша).
        """Проверить валидность ставки"""
        if bet_amount <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительным числом!")
            return False
        
        if bet_amount > user_balance:
            await update.message.reply_text("❌ Недостаточно средств на балансе!")
            return False
        
        return True
    
    @staticmethod
    def validate_dice_number(number: int) -> bool:
        """Проверить число для ставки в костях"""
        return 2 <= number <= 12
    
    @staticmethod
    def validate_roulette_number(number: int) -> bool:
        """Проверить число для ставки в рулетке"""
        return 0 <= number <= 36
    
    @staticmethod
    async def validate_game_input(update: Update, input_type: str, value: int) -> bool:
        """Универсальная проверка игрового ввода"""
        validators = {
            "dice_number": lambda x: 2 <= x <= 12,
            "roulette_number": lambda x: 0 <= x <= 36,
            "bet_amount": lambda x: x > 0
        }
        
        validator = validators.get(input_type)
        if not validator or not validator(value):
            error_messages = {
                "dice_number": "❌ Число должно быть от 2 до 12!",
                "roulette_number": "❌ Число должно быть от 0 до 36!",
                "bet_amount": "❌ Ставка должна быть положительным числом!"
            }
            await update.message.reply_text(error_messages.get(input_type, "❌ Неверный ввод!"))
            return False
        
        return True
