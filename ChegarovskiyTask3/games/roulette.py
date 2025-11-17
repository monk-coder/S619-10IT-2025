"""
Класс игры в рулетку
"""
import random
from .base import Game
from typing import Union

class Roulette(Game):
    """Класс для игры в рулетку"""
    
    NUMBERS = list(range(0, 37))  # Европейская рулетка: 0-36
    RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    
    def __init__(self):
        super().__init__()
        self.winning_number = 0
        self.bet_type = ""
        self.bet_value = None
        
    def play(self, bet_amount: int, bet_type: str, bet_value: Union[int, str]) -> Tuple[int, int]:
        """Сыграть в рулетку"""
        self.bet_amount = bet_amount
        self.bet_type = bet_type
        self.bet_value = bet_value
        
        self._spin_wheel()
        win_amount = self._calculate_payout()
        return self.winning_number, win_amount
    
    def _spin_wheel(self):
        """Крутить рулетку"""
        self.winning_number = random.choice(self.NUMBERS)
    
    def _calculate_payout(self) -> int:
        """Рассчитать выигрыш для ставки"""
        payout_multipliers = {
            "number": 36,
            "color": 2, 
            "even_odd": 2
        }
        
        multiplier = payout_multipliers.get(self.bet_type, 0)
        is_win = self._check_win_condition()
        
        return self.calculate_win_amount(multiplier) if is_win else 0
    
    def _check_win_condition(self) -> bool:
        """Проверить условие выигрыша"""
        match self.bet_type:
            case "number":
                return self.bet_value == self.winning_number
            case "color":
                return self._check_color_win()
            case "even_odd":
                return self._check_even_odd_win()
            case _:
                return False
    
    def _check_color_win(self) -> bool:
        """Проверить выигрыш по цвету"""
        if self.winning_number == 0:
            return False
        
        is_red = self.winning_number in self.RED_NUMBERS
        return (self.bet_value == "red" and is_red) or (self.bet_value == "black" and not is_red)
    
    def _check_even_odd_win(self) -> bool:
        """Проверить выигрыш по чётности"""
        if self.winning_number == 0:
            return False
        
        is_even = self.winning_number % 2 == 0
        return (self.bet_value == "even" and is_even) or (self.bet_value == "odd" and not is_even)
    
    def get_winning_color(self) -> str:
        """Получить цвет выпавшего числа"""
        if self.winning_number == 0:
            return "green"
        return "red" if self.winning_number in self.RED_NUMBERS else "black"
