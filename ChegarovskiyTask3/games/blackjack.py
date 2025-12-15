"""
Класс игры в блекджек
"""
import random
from .base import Game
from typing import List, Tuple

class Blackjack(Game):
    """Класс для игры в блекджек"""
    
    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
        '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    CARD_SUITS = ['♠', '♥', '♦', '♣']
    
    def __init__(self):
        super().__init__()
        self.deck = self._create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.player_value = 0
        self.dealer_value = 0
        random.shuffle(self.deck)
    
    def play(self, bet_amount: int, **kwargs) -> Tuple[str, int]:
        """Начать новую игру в блекджек
        
        Возвращает: (результат, выигрыш)
        """
        self.bet_amount = bet_amount
        self.player_hand = [self._deal_card(), self._deal_card()]
        self.dealer_hand = [self._deal_card(), self._deal_card()]
        
        # Возвращаем результат игры (как и другие игры)
        return self.get_game_result()
    
    def _create_deck(self) -> List[Tuple[str, str]]:
        """Создать новую колоду карт"""
        return [(value, suit) for value in self.CARD_VALUES for suit in self.CARD_SUITS] * 4
    
    def _deal_card(self) -> Tuple[str, str]:
        """Раздать одну карту из колоды"""
        if not self.deck:
            self.deck = self._create_deck()
            random.shuffle(self.deck)
        return self.deck.pop()
    
    def calculate_hand_value(self, hand: List[Tuple[str, str]]) -> int:
        """Посчитать стоимость руки с корректной обработкой тузов"""
        value = sum(self.CARD_VALUES[card[0]] for card in hand)
        aces_count = sum(1 for card in hand if card[0] == 'A')
        
        # Корректируем стоимость тузов если перебор
        while value > 21 and aces_count > 0:
            value -= 10  # Тузы из 11 очков становятся 1 очком
            aces_count -= 1
            
        return value
    
    def player_hit(self) -> None:
        """Игрок берет дополнительную карту"""
        card = self._deal_card()
        self.player_hand.append(card)
    
    def dealer_play(self):
        """Дилер добирает карты по правилам"""
        self.dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        while self.dealer_value < 17:
            self.dealer_hand.append(self._deal_card())
            self.dealer_value = self.calculate_hand_value(self.dealer_hand)
    
    def get_game_result(self) -> Tuple[str, int]:
        """Определить результат игры"""
        self.player_value = self.calculate_hand_value(self.player_hand)
        self.dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        if self.player_value > 21:
            return "lose", -self.bet_amount
        elif self.dealer_value > 21 or self.player_value > self.dealer_value:
            return "win", self.bet_amount
        elif self.player_value < self.dealer_value:
            return "lose", -self.bet_amount
        else:
            return "push", 0
