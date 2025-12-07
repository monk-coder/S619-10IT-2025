"""
Инициализация игрового модуля
Экспорт всех игровых классов
"""
from .slots import SlotMachine
from .dice import DiceGame
from .blackjack import Blackjack
from .roulette import Roulette

__all__ = ['SlotMachine', 'DiceGame', 'Blackjack', 'Roulette']
