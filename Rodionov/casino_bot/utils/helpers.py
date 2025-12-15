# utils/helpers.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_balance(balance: int) -> str:
    """Форматирование баланса для красивого отображения"""
    try:
        return f"{balance:,} 🪙".replace(",", " ")
    except (TypeError, ValueError):
        return "0 🪙"

def validate_bet(bet_str: str, min_bet: int, max_bet: int, balance: int) -> tuple:
    """Проверка валидности ставки"""
    try:
        bet = int(bet_str)

        if bet < min_bet:
            return False, f"Минимальная ставка: {min_bet} 🪙"

        if bet > max_bet:
            return False, f"Максимальная ставка: {max_bet} 🪙"

        if bet > balance:
            return False, "Недостаточно средств на балансе"

        return True, "Ставка принята"

    except ValueError:
        return False, "Введите корректное число"

def get_time_based_greeting() -> str:
    """Получить приветствие в зависимости от времени суток"""
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"

def format_game_result(is_win: bool, amount: int, game_type: str) -> str:
    """Форматирование результата игры"""
    if is_win:
        return f"🎉 ПОБЕДА! +{amount} 🪙 в {game_type}"
    else:
        return f"😞 ПРОИГРЫШ {amount} 🪙 в {game_type}"