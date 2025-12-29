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
        
    def play(self, bet_amount: int, prediction: str = None, number: int = None) -> Tuple[str, int]:
        """Бросок костей и расчет выигрыша
        
        Args:
            bet_amount: сумма ставки
            prediction: тип ставки ("even", "odd", "number", "double")
            number: число для ставки "number" (от 2 до 12)
            
        Returns:
            Tuple[str, int]: (результат_описанием, выигрыш)
            
        Правильная реализация абстрактного метода:
        1. Принимает bet_amount первым (обязательно)
        2. Остальное через **kwargs
        3. Возвращает (результат, выигрыш)
        """
        # Сохраняем ставку как требует базовый класс
        self.bet_amount = bet_amount
        
        # Если передали параметры - используем их
        if prediction is not None:
            self._roll_dice()
            self._calculate_win(prediction, number)
            
            # Формируем результат как строка
            result_text = f"Кости: {self.dice1}+{self.dice2}={self.total}"
            
            # Возвращаем как требует абстрактный класс
            return result_text, self.win_amount
        else:
            # Для совместимости - если вызвали без параметров
            # (но так не должно быть)
            self._roll_dice()
            return f"Кости: {self.dice1}+{self.dice2}={self.total}", 0
    
    def _roll_dice(self):
        """Бросить два кубика"""
        self.dice1 = random.randint(1, 6)
        self.dice2 = random.randint(1, 6)
        self.total = self.dice1 + self.dice2
    
    def _calculate_win(self, prediction: str, number: int = None):
        """Рассчитать выигрыш на основе ставки"""
        multipliers = {
            "even": 2, "odd": 2, "number": 6, "double": 8
        }
        
        is_win = self._check_win_condition(prediction, number)
        multiplier = multipliers.get(prediction, 0) if is_win else 0
        self.win_amount = self.calculate_win_amount(multiplier)
    
    def _check_win_condition(self, prediction: str, number: int = None) -> bool:
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
