"""Логика игры в блекджек"""
import random
from typing import List, Tuple

class Blackjack:
    """Класс для игры в блекджек"""

    VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    SUITS = ['♠', '♥', '♦', '♣']

    def __init__(self):
        self.deck = self._create_deck()
        random.shuffle(self.deck)

    def _create_deck(self) -> List[Tuple[str, str]]:
        """Создать колоду карт"""
        return [(value, suit) for value in self.VALUES for suit in self.SUITS] * 4

    def deal_card(self) -> Tuple[str, str]:
        """Раздать карту из колоды"""
        if not self.deck:
            self.deck = self._create_deck()
            random.shuffle(self.deck)
        return self.deck.pop()

    def calculate_hand_value(self, hand: List[Tuple[str, str]]) -> int:
        """Посчитать стоимость руки"""
        value = sum(self.VALUES[card[0]] for card in hand)
        aces = sum(1 for card in hand if card[0] == 'A')

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value