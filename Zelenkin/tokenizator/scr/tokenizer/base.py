"""Базовые классы и интерфейсы для токенизатора."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field


@dataclass
class TokenizerConfig:
    """Конфигурация токенизатора."""

    num_merges: int = 8000
    special_tokens: List[str] = field(default_factory=lambda: ["<PAD>", "<UNK>", "<BOS>", "<EOS>"])
    lowercase: bool = True
    strip_accents: bool = False
    max_word_length: Optional[int] = None
    min_frequency: int = 1


class BaseTokenizer(ABC):
    """Абстрактный базовый класс для токенизатора."""

    @abstractmethod
    def train(self, corpus: List[str], config: TokenizerConfig) -> 'BaseTokenizer':
        """Обучение токенизатора на корпусе."""
        pass

    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """Кодирование текста в последовательность ID."""
        pass

    @abstractmethod
    def decode(self, ids: List[int]) -> str:
        """Декодирование ID обратно в текст."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Сохранение токенизатора."""
        pass

    @abstractmethod
    def load(self, path: str) -> 'BaseTokenizer':
        """Загрузка токенизатора."""
        pass

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """Размер словаря."""
        pass

    @property
    @abstractmethod
    def merges_count(self) -> int:
        """Количество правил слияния."""
        pass