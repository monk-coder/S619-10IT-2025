"""
Базовый класс для всех игр
Содержит общую логику ставок и результатов
"""
from abc import ABC, abstractmethod
from typing import Tuple, Any

class Game(ABC):
    """Абстрактный базовый класс для всех игр казино"""
    
    def __init__(self):
        self.bet_amount = 0
        self.result = None
        
    @abstractmethod
    def play(self, bet_amount: int, **kwargs) -> Tuple[Any, int]:
        pass
    
    def calculate_win_amount(self, multiplier: int) -> int:
        return self.bet_amount * multiplier
    
    def validate_bet(self, user_balance: int, bet_amount: int) -> bool:
        return 0 < bet_amount <= user_balance
