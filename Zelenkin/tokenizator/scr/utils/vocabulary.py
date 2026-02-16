"""Класс для управления словарем токенов."""

from typing import Dict, List, Optional
from collections import OrderedDict


class Vocabulary:
    """
    Управление словарем токенов.
    Отвечает за маппинг токен <-> ID.
    """

    def __init__(self):
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.special_tokens: Dict[str, int] = {}

    def initialize(self, tokens: set, special_tokens: List[str]) -> None:
        """
        Инициализация словаря.

        Args:
            tokens: множество начальных токенов (символов)
            special_tokens: список специальных токенов
        """
        next_id = 0

        # Добавляем специальные токены
        for token in special_tokens:
            if token not in self.token_to_id:
                self.token_to_id[token] = next_id
                self.id_to_token[next_id] = token
                self.special_tokens[token] = next_id
                next_id += 1

        # Добавляем обычные токены
        for token in sorted(tokens):
            if token not in self.token_to_id:
                self.token_to_id[token] = next_id
                self.id_to_token[next_id] = token
                next_id += 1

    def add_token(self, token: str) -> int:
        """
        Добавление нового токена в словарь.

        Args:
            token: токен для добавления

        Returns:
            ID добавленного токена
        """
        if token in self.token_to_id:
            return self.token_to_id[token]

        new_id = len(self.token_to_id)
        self.token_to_id[token] = new_id
        self.id_to_token[new_id] = token
        return new_id

    def get_id(self, token: str, default: Optional[int] = None) -> Optional[int]:
        """Получение ID токена."""
        return self.token_to_id.get(token, default)

    def get_token(self, token_id: int, default: Optional[str] = None) -> Optional[str]:
        """Получение токена по ID."""
        return self.id_to_token.get(token_id, default)

    def __len__(self) -> int:
        return len(self.token_to_id)

    def __contains__(self, token: str) -> bool:
        return token in self.token_to_id

    def to_dict(self) -> Dict:
        """Сериализация словаря."""
        return {
            'token_to_id': self.token_to_id,
            'special_tokens': self.special_tokens
        }

    def from_dict(self, data: Dict) -> None:
        """Десериализация словаря."""
        self.token_to_id = data['token_to_id']
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}
        self.special_tokens = data['special_tokens']