"""Логика игры в слоты"""
import random
from typing import List, Tuple

class SlotMachine:
    """Класс для игры в слоты"""

    SYMBOLS = ["🍒", "🍋", "🍊", "💎", "7", "🍀"]
    PAYOUTS = {
        "three_same": 5,
        "two_same": 2
    }

    @staticmethod
    def spin() -> Tuple[List[str], int]:
        """Крутить слоты и вернуть результат и множитель выигрыша"""
        reels = [random.choice(SlotMachine.SYMBOLS) for _ in range(3)]

        # Проверка комбинаций
        if reels[0] == reels[1] == reels[2]:
            multiplier = SlotMachine.PAYOUTS["three_same"]
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            multiplier = SlotMachine.PAYOUTS["two_same"]
        else:
            multiplier = 0

        return reels, multiplier