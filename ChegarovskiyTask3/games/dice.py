"""Логика игры в кости"""
import random
from typing import Tuple

class DiceGame:
    """Класс для игры в кости"""

    @staticmethod
    def roll(bet: int, prediction: str, number: int = None) -> Tuple[int, int, int, int]:
        """Бросок костей и расчет выигрыша"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        if prediction == "even" and total % 2 == 0:
            win_amount = bet * 2
        elif prediction == "odd" and total % 2 == 1:
            win_amount = bet * 2
        elif prediction == "number" and number == total:
            win_amount = bet * 6
        elif prediction == "double" and dice1 == dice2:
            win_amount = bet * 8
        else:
            win_amount = 0

        return dice1, dice2, total, win_amount