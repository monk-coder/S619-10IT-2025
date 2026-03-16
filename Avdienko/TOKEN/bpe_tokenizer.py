import json
import pickle
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import numpy as np
import regex as re


class BPETokenizer:
    def __init__(self):
        self.vocab = {}  # token -> id
        self.id_to_token = {}  # id -> token
        self.merges = {}  # (token1, token2) -> merged_token
        self.pattern = r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""
        self.compiled_pattern = re.compile(self.pattern)

    @classmethod
    def train(cls, corpus: List[str], num_merges: int,
              special_tokens: Optional[List[str]] = None,
              verbose: bool = True) -> 'BPETokenizer':
        """Обучает BPE токенизатор на корпусе текстов."""
        tokenizer = cls()

        # Добавляем специальные токены
        if special_tokens is None:
            special_tokens = []

        # Инициализация словаря символов
        word_freqs = Counter()
        for text in corpus:
            words = tokenizer._split_text(text)
            word_freqs.update(words)

        # Создаем начальный словарь
        tokenizer._initialize_vocab(word_freqs, special_tokens)

        # Применяем BPE слияния
        tokenizer._apply_merges(word_freqs, num_merges, verbose)

        return tokenizer

    def _split_text(self, text: str) -> List[str]:
        """Разбивает текст на слова с помощью регулярного выражения."""
        return self.compiled_pattern.findall(text)

    def _initialize_vocab(self, word_freqs: Counter, special_tokens: List[str]):
        """Инициализирует словарь уникальными символами."""
        # Добавляем специальные токены
        for token in special_tokens:
            if token not in self.vocab:
                idx = len(self.vocab)
                self.vocab[token] = idx
                self.id_to_token[idx] = token

        # Собираем все уникальные символы
        chars = set()
        for word in word_freqs:
            chars.update(word)

        # Добавляем символы в словарь
        for char in sorted(chars):
            if char not in self.vocab:
                idx = len(self.vocab)
                self.vocab[char] = idx
                self.id_to_token[idx] = char

    def _apply_merges(self, word_freqs: Counter, num_merges: int, verbose: bool = True):
        """Применяет BPE слияния для создания новых токенов."""
        # Преобразуем слова в списки символов
        vocab_words = {}
        for word, freq in word_freqs.items():
            vocab_words[word] = (list(word), freq)

        from tqdm import tqdm

        for i in tqdm(range(num_merges), desc="BPE merges", disable=not verbose):
            # Подсчитываем частоты пар
            pair_freqs = self._get_pair_frequencies(vocab_words)

            if not pair_freqs:
                break

            # Находим самую частую пару
            best_pair = max(pair_freqs, key=pair_freqs.get)

            # Создаем новый токен
            new_token = best_pair[0] + best_pair[1]

            # Добавляем новый токен в словарь
            if new_token not in self.vocab:
                idx = len(self.vocab)
                self.vocab[new_token] = idx
                self.id_to_token[idx] = new_token

            # Сохраняем правило слияния
            self.merges[best_pair] = new_token

            # Обновляем слова слов
            self._merge_pair_in_vocab(vocab_words, best_pair, new_token)

    def _get_pair_frequencies(self, vocab_words: Dict) -> Dict[Tuple[str, str], int]:
        """Подсчитывает частоты соседних пар токенов."""
        pair_freqs = defaultdict(int)

        for tokens, freq in vocab_words.values():
            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                pair_freqs[pair] += freq

        return pair_freqs

    def _merge_pair_in_vocab(self, vocab_words: Dict, pair: Tuple[str, str], new_token: str):
        """Объединяет указанную пару токенов во всем словаре."""
        for word, (tokens, freq) in vocab_words.items():
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                    new_tokens.append(new_token)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            vocab_words[word] = (new_tokens, freq)

    def encode(self, text: str) -> List[int]:
        """Кодирует текст в последовательность ID токенов."""
        # Разбиваем текст на слова
        words = self._split_text(text)

        # Токенизируем каждое слово
        token_ids = []
        for word in words:
            # Начинаем с символов
            tokens = list(word)

            # Применяем слияния
            while len(tokens) > 1:
                # Находим пару с наивысшим приоритетом (самое раннее слияние)
                min_pair = None
                min_rank = float('inf')

                for i in range(len(tokens) - 1):
                    pair = (tokens[i], tokens[i + 1])
                    if pair in self.merges:
                        # Проверяем, является ли это слияние допустимым
                        # (не нарушает ли другие возможные слияния)
                        if self._can_merge(tokens, i, pair):
                            # Используем порядок добавления в merges как приоритет
                            rank = list(self.merges.keys()).index(pair) if pair in self.merges else float('inf')
                            if rank < min_rank:
                                min_rank = rank
                                min_pair = (i, pair)

                if min_pair is None:
                    break

                i, pair = min_pair
                new_token = self.merges[pair]
                tokens = tokens[:i] + [new_token] + tokens[i + 2:]

            # Добавляем ID токенов в результат
            for token in tokens:
                if token in self.vocab:
                    token_ids.append(self.vocab[token])
                else:
                    # Если токен не найден (маловероятно), разбиваем на символы
                    for char in token:
                        token_ids.append(self.vocab[char])

        return token_ids

    def _can_merge(self, tokens: List[str], idx: int, pair: Tuple[str, str]) -> bool:
        """Проверяет, можно ли выполнить слияние пары на данной позиции."""
        # Базовый случай - всегда можно, если пара есть в merges
        return True

    def decode(self, token_ids: List[int]) -> str:
        """Декодирует последовательность ID токенов обратно в текст."""
        # Преобразуем ID в токены
        tokens = [self.id_to_token.get(idx, '') for idx in token_ids]

        # Объединяем токены
        result = ''.join(tokens)

        return result

    def save(self, path: str):
        """Сохраняет токенизатор в файл."""
        with open(path, 'wb') as f:
            pickle.dump({
                'vocab': self.vocab,
                'id_to_token': self.id_to_token,
                'merges': self.merges,
                'pattern': self.pattern
            }, f)

    def save_merges_json(self, path: str):
        """Сохраняет правила слияний в JSON файл."""
        # Преобразуем кортежи в строки для JSON
        merges_json = {}
        for (t1, t2), merged in self.merges.items():
            key = f"{t1} {t2}"
            merges_json[key] = merged

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(merges_json, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> 'BPETokenizer':
        """Загружает токенизатор из файла."""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        tokenizer = cls()
        tokenizer.vocab = data['vocab']
        tokenizer.id_to_token = data['id_to_token']
        tokenizer.merges = data['merges']
        tokenizer.pattern = data.get('pattern', tokenizer.pattern)
        tokenizer.compiled_pattern = re.compile(tokenizer.pattern)

        return tokenizer

    @property
    def vocab_size(self) -> int:
        """Возвращает размер словаря."""
        return len(self.vocab)

    def tokenize(self, text: str) -> List[str]:
        """Токенизирует текст и возвращает список токенов."""
        ids = self.encode(text)
        return [self.id_to_token[idx] for idx in ids]