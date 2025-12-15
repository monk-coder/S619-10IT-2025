"""
Класс игры в слоты
Наследует общую логику от базового класса Game
"""
import random
from .base import Game
from typing import List, Tuple

class SlotMachine(Game):
    """Класс для игры в слот-машину"""
    
    SYMBOLS = ["🍒", "🍋", "🍊", "💎", "7", "🍀"]
    PAYOUTS = {"three_same": 5, "two_same": 2}
    
    def __init__(self):
        super().__init__()
        self.reels = []
        self.multiplier = 0
        
    def play(self, bet_amount: int) -> Tuple[List[str], int]:
        """Основной игровой метод - крутить слоты"""
        self.bet_amount = bet_amount
        self._spin_reels()
        self._calculate_multiplier()
        return self.reels, self.multiplier
    
    def _spin_reels(self):
        """Крутить барабаны слотов"""
        self.reels = [self._get_random_symbol() for _ in range(3)]
    
    def _get_random_symbol(self) -> str:
        """Получить случайный символ"""
        return random.choice(self.SYMBOLS)
    
    def _calculate_multiplier(self):
        """Рассчитать множитель выигрыша на основе комбинации"""
        if self.reels[0] == self.reels[1] == self.reels[2]:
            self.multiplier = self.PAYOUTS["three_same"]
        elif self.reels[0] == self.reels[1] or self.reels[1] == self.reels[2] or self.reels[0] == self.reels[2]:
            self.multiplier = self.PAYOUTS["two_same"]
        else:
            self.multiplier = 0
    
    def get_win_amount(self) -> int:
        """Получить сумму выигрыша"""
        return self.calculate_win_amount(self.multiplier)
