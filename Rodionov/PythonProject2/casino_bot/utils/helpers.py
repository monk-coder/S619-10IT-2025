# utils/helpers.py
import random
from datetime import datetime

def format_balance(balance: int) -> str:
    """Форматирование баланса"""
    if balance is None:
        return "0 🪙"
    return f"{balance:,} 🪙".replace(",", " ")


def validate_bet(bet: str, min_bet: int, max_bet: int, user_balance: int) -> tuple:
    """Валидация ставки"""
    try:
        bet_amount = int(bet)
        if bet_amount < min_bet:
            return False, f"Минимальная ставка: {min_bet} монет"
        if bet_amount > max_bet:
            return False, f"Максимальная ставка: {max_bet} монет"
        if user_balance is None or bet_amount > user_balance:
            return False, "Недостаточно средств на балансе"
        return True, bet_amount
    except ValueError:
        return False, "Пожалуйста, введите число"





def get_time_based_greeting() -> str:
    """Приветствие в зависимости от времени суток"""
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def format_time_remaining(seconds: int) -> str:
    """Форматирование оставшегося времени"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}ч {minutes}м"