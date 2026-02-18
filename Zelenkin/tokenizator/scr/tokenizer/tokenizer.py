"""Основной класс BPE токенизатора."""

import json
from typing import List, Dict, Optional, Union
from pathlib import Path

from .base import BaseTokenizer, TokenizerConfig
from .bpe_core import BPECore
from ..utils.vocabulary import Vocabulary
from ..utils.data_loader import TextPreprocessor


class BPETokenizer(BaseTokenizer):
    """
    BPE токенизатор с полным функционалом.
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()
        self.core = BPECore()
        self.vocab = Vocabulary()
        self.preprocessor = TextPreprocessor(
            lowercase=self.config.lowercase,
            strip_accents=self.config.strip_accents
        )
        
    def train(self, corpus: List[str], config: Optional[TokenizerConfig] = None) -> 'BPETokenizer':
        """
        Обучение токенизатора.
        
        Args:
            corpus: список текстов для обучения
            config: конфигурация (если не указана, используется сохраненная)
            
        Returns:
            self
        """
        if config:
            self.config = config
            
        # Предобработка текстов
        processed_corpus = [self.preprocessor.process(text) for text in corpus]
        
        # Подсчет частот слов
        word_counts = self._get_word_frequencies(processed_corpus)
        
        # Получаем начальные символы
        initial_chars = self.core.get_initial_vocab(word_counts)
        
        # ВАЖНО: Добавляем пробел в словарь принудительно (уже есть в get_initial_vocab)
        
        # Инициализация словаря символами
        self.vocab = Vocabulary(initial_chars, self.config.special_tokens)
        
        # Обучение слияниям
        self._learn_merges(word_counts, self.config.num_merges)
        
        return self
    
    def _get_word_frequencies(self, corpus: List[str]) -> Dict[str, int]:
        """Подсчет частот слов в корпусе."""
        word_counts = {}
        
        for text in corpus:
            # Разбиваем по пробелам, чтобы сохранить информацию о словах
            words = text.split()
            for word in words:
                if len(word) <= (self.config.max_word_length or float('inf')):
                    # Представляем слово как последовательность символов с пробелами
                    word_with_spaces = ' '.join(word)
                    word_counts[word_with_spaces] = word_counts.get(word_with_spaces, 0) + 1
                    
        return word_counts
    
    def _learn_merges(self, word_counts: Dict[str, int], num_merges: int) -> None:
        """Обучение правил слияния."""
        current_word_counts = word_counts.copy()
        
        for _ in range(num_merges):
            # Подсчет пар
            pairs = self.core.get_stats(current_word_counts)
            
            if not pairs:
                break
                
            # Выбор лучшей пары
            best_pair = max(pairs, key=pairs.get)
            
            # Применение слияния
            current_word_counts = self.core.merge_vocab(best_pair, current_word_counts)
            
            # Сохранение правила
            self.core.merges.append(best_pair)
            
            # Добавление нового токена в словарь
            new_token = best_pair[0] + best_pair[1]
            if new_token not in self.vocab:
                self.vocab.add_token(new_token)
    
    def _token_to_id(self, token: str) -> List[int]:
        """
        Преобразует токен в ID (или список ID, если токен неизвестен).
        
        Args:
            token: входной токен
            
        Returns:
            список ID для этого токена
        """
        # 1. Пробуем найти токен целиком
        token_id = self.vocab.get_id(token)
        if token_id is not None:
            return [token_id]
        
        # 2. Если токен не найден, пробуем разбить на символы
        char_ids = []
        for char in token:
            char_id = self.vocab.get_id(char)
            if char_id is not None:
                char_ids.append(char_id)
            else:
                # 3. Если символ не найден, используем UNK
                unk_id = self.vocab.get_id('<UNK>')
                if unk_id is not None:
                    char_ids.append(unk_id)
        
        return char_ids if char_ids else []
    
    def encode(self, text: str) -> List[int]:
        """
        Кодирование текста в ID токенов с сохранением пробелов.
        
        Args:
            text: входной текст
            
        Returns:
            список ID
        """
        if not text:
            return []
        
        # Предобработка
        text = self.preprocessor.process(text)
        
        # Разбиваем на слова, СОХРАНЯЕМ ПРОБЕЛЫ
        words = text.split(' ')
        
        token_ids = []
        
        for i, word in enumerate(words):
            if not word:
                continue
                
            # Применяем BPE к слову
            tokens = self.core.tokenize_word(word, self.core.merges)
            
            # Конвертируем каждый токен в ID (используем новую функцию)
            for token in tokens:
                token_ids.extend(self._token_to_id(token))
            
            # Добавляем пробел между словами (кроме последнего)
            if i < len(words) - 1:
                space_id = self.vocab.get_id(' ')
                if space_id is not None:
                    token_ids.append(space_id)
        
        return token_ids
    
    def decode(self, ids: List[int]) -> str:
        """
        Декодирование ID обратно в текст с пробелами.
        
        Args:
            ids: список ID
            
        Returns:
            восстановленный текст
        """
        if not ids:
            return ""
        
        # Декодируем токены
        tokens = []
        for token_id in ids:
            token = self.vocab.get_token(token_id)
            if token is not None:
                tokens.append(token)
            else:
                tokens.append('<UNK>')
        
        # Склеиваем (пробелы уже есть как отдельные токены)
        text = ''.join(tokens)
        
        return text
    
    def save(self, path: Union[str, Path]) -> None:
        """
        Сохранение токенизатора.
        
        Args:
            path: путь для сохранения
        """
        save_dict = {
            'config': {
                'num_merges': self.config.num_merges,
                'special_tokens': self.config.special_tokens,
                'lowercase': self.config.lowercase,
                'strip_accents': self.config.strip_accents,
                'max_word_length': self.config.max_word_length,
                'min_frequency': self.config.min_frequency
            },
            'merges': [(m[0], m[1]) for m in self.core.merges],
            'vocab': self.vocab.to_dict()
        }
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_dict, f, ensure_ascii=False, indent=2)
    
    def load(self, path: Union[str, Path]) -> 'BPETokenizer':
        """
        Загрузка токенизатора.
        
        Args:
            path: путь к файлу
            
        Returns:
            self
        """
        with open(path, 'r', encoding='utf-8') as f:
            save_dict = json.load(f)
        
        # Восстановление конфигурации
        config_dict = save_dict['config']
        self.config = TokenizerConfig(
            num_merges=config_dict['num_merges'],
            special_tokens=config_dict['special_tokens'],
            lowercase=config_dict['lowercase'],
            strip_accents=config_dict['strip_accents'],
            max_word_length=config_dict['max_word_length'],
            min_frequency=config_dict['min_frequency']
        )
        
        # Восстановление слияний
        self.core.merges = [(m[0], m[1]) for m in save_dict['merges']]
        
        # Восстановление словаря
        self.vocab = Vocabulary()
        self.vocab.from_dict(save_dict['vocab'])
        
        # Восстановление препроцессора
        self.preprocessor = TextPreprocessor(
            lowercase=self.config.lowercase,
            strip_accents=self.config.strip_accents
        )
        
        return self
    
    @property
    def vocab_size(self) -> int:
        return len(self.vocab)
    
    @property
    def merges_count(self) -> int:
        return len(self.core.merges)
