"""
Класс игры в кости
"""
import random
from .base import Game
from typing import Tuple

class DiceGame(Game):
    """Класс для игры в кости"""
    
    def __init__(self):
        super().__init__()
        self.dice1 = 0
        self.dice2 = 0
        self.total = 0
        self.win_amount = 0
        
    def play(self, bet_amount: int, prediction: str, number: int = None) -> Tuple[int, int, int, int]:
        """Бросок костей и расчет выигрыша"""
        self.bet_amount = bet_amount
        self._roll_dice()
        self._calculate_win(prediction, number)
        return self.dice1, self.dice2, self.total, self.win_amount
    
    def _roll_dice(self):
        """Бросить два кубика"""
        self.dice1 = random.randint(1, 6)
        self.dice2 = random.randint(1, 6)
        self.total = self.dice1 + self.dice2
    
    def _calculate_win(self, prediction: str, number: int):
        """Рассчитать выигрыш на основе ставки"""
        multipliers = {
            "even": 2, "odd": 2, "number": 6, "double": 8
        }
        
        is_win = self._check_win_condition(prediction, number)
        multiplier = multipliers.get(prediction, 0) if is_win else 0
        self.win_amount = self.calculate_win_amount(multiplier)
    
    def _check_win_condition(self, prediction: str, number: int) -> bool:
        """Проверить условие выигрыша"""
        if prediction == "even":
            return self.total % 2 == 0
        elif prediction == "odd":
            return self.total % 2 == 1
        elif prediction == "number":
            return number == self.total
        elif prediction == "double":
            return self.dice1 == self.dice2
        return False
