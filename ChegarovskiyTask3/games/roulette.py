"""Логика игры в рулетку"""
import random
from typing import List


class Roulette:
    """Класс для игры в рулетку"""

    NUMBERS = list(range(0, 37))  # 0-36
    RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

    @staticmethod
    def spin() -> int:
        """Крутить рулетку"""
        return random.choice(Roulette.NUMBERS)

    @staticmethod
    def calculate_payout(bet_type: str, bet_number: int, winning_number: int) -> int:
        """Рассчитать выигрыш для ставки"""
        if bet_type == "number":
            return 36 if bet_number == winning_number else 0
        elif bet_type == "color":
            is_red = winning_number in Roulette.RED_NUMBERS
            return 2 if (bet_number == "red" and is_red) or (bet_number == "black" and not is_red) else 0
        elif bet_type == "even_odd":
            if winning_number == 0:
                return 0
            is_even = winning_number % 2 == 0
            return 2 if (bet_number == "even" and is_even) or (bet_number == "odd" and not is_even) else 0
        return 0