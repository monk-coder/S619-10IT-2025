import json
import re
import os
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import numpy as np
from tqdm import tqdm


class BPETokenizer:
    def __init__(self):
        """
        Инициализация BPE токенизатора.
        """
        self.vocab = {}  # id -> токен
        self.vocab_inverse = {}  # токен -> id
        self.merges = []  # Правила слияний
        self.merge_rules = {}  # Для быстрого поиска
        self.vocab_size = 0
        self.special_tokens = ['<unk>', '<pad>', '<s>', '</s>', '</w>']

    def _get_words(self, text: str) -> List[str]:
        """
        Простая токенизация на слова.
        """
        # Более простая реализация без regex
        words = []
        current_word = []

        for char in text:
            if char.isalnum() or char in "'-":
                current_word.append(char)
            else:
                if current_word:
                    words.append(''.join(current_word))
                    current_word = []
                if char.strip():  # Не-пробельные символы как отдельные токены
                    words.append(char)

        if current_word:
            words.append(''.join(current_word))

        return words

    def train(self, corpus: List[str], num_merges: int = 1000, verbose: bool = True):
        """
        Обучение BPE токенизатора на корпусе текстов.
        """
        if verbose:
            print(f"Начало обучения BPE с {num_merges} слияниями...")

        # Шаг 1: Предобработка текста и получение слов
        word_counts = Counter()
        for text in corpus:
            words = self._get_words(text)
            word_counts.update(words)

        if verbose:
            print(f"Найдено {len(word_counts)} уникальных слов")
            print(f"Всего слов в корпусе: {sum(word_counts.values())}")

        # Шаг 2: Инициализация словаря символов
        self._init_vocab(word_counts)

        # Шаг 3: Представление слов как последовательности символов
        word_representations = {}
        for word in word_counts:
            # Добавляем </w> для обозначения конца слова
            word_representations[word] = list(word) + ['</w>']

        # Шаг 4: Итеративные слияния
        for i in tqdm(range(num_merges), desc="Обучение BPE", disable=not verbose):
            # Подсчет частот пар
            pair_freqs = self._get_pair_frequencies(word_representations, word_counts)

            if not pair_freqs:
                if verbose:
                    print(f"Нет больше пар для слияния на шаге {i}")
                break

            # Находим самую частую пару
            most_frequent_pair = max(pair_freqs, key=pair_freqs.get)

            # Добавляем правило слияния
            self._add_merge_rule(most_frequent_pair)

            # Обновляем представления слов
            self._apply_merge(word_representations, most_frequent_pair)

        # Создаем финальный словарь
        self._create_final_vocab()

        if verbose:
            print(f"\nОбучение завершено!")
            print(f"Размер словаря: {self.vocab_size}")
            print(f"Количество правил слияния: {len(self.merges)}")

    def _init_vocab(self, word_counts: Counter):
        """Инициализация словаря символами из корпуса."""
        # Собираем все уникальные символы
        chars = set()
        for word in word_counts:
            chars.update(word)

        # Создаем словарь
        self.vocab = {}
        self.vocab_inverse = {}

        # Добавляем специальные токены
        for i, token in enumerate(self.special_tokens):
            self.vocab[i] = token
            self.vocab_inverse[token] = i

        # Добавляем символы в алфавитном порядке для воспроизводимости
        for char in sorted(chars):
            if char not in self.vocab_inverse:
                idx = len(self.vocab)
                self.vocab[idx] = char
                self.vocab_inverse[char] = idx

        self.vocab_size = len(self.vocab)

    def _get_pair_frequencies(self, word_representations: Dict, word_counts: Counter) -> Dict[Tuple, int]:
        """Подсчет частот соседних пар токенов."""
        pair_freqs = defaultdict(int)

        for word, representation in word_representations.items():
            count = word_counts[word]

            for i in range(len(representation) - 1):
                pair = (representation[i], representation[i + 1])
                pair_freqs[pair] += count

        return dict(pair_freqs)

    def _add_merge_rule(self, pair: Tuple[str, str]):
        """Добавление нового правила слияния."""
        new_token = pair[0] + pair[1]
        self.merges.append(pair)
        self.merge_rules[pair] = new_token

        # Временно добавляем новый токен в словарь
        if new_token not in self.vocab_inverse:
            idx = len(self.vocab)
            self.vocab[idx] = new_token
            self.vocab_inverse[new_token] = idx

    def _apply_merge(self, word_representations: Dict, pair: Tuple[str, str]):
        """Применение слияния ко всем словам."""
        new_token = self.merge_rules[pair]

        for word, representation in word_representations.items():
            i = 0
            new_representation = []

            while i < len(representation):
                if i < len(representation) - 1 and (representation[i], representation[i + 1]) == pair:
                    new_representation.append(new_token)
                    i += 2
                else:
                    new_representation.append(representation[i])
                    i += 1

            word_representations[word] = new_representation

    def _create_final_vocab(self):
        """Создание финального словаря после всех слияний."""
        # Переиндексируем словарь для последовательных id
        all_tokens = set(self.vocab.values())
        self.vocab = {}
        self.vocab_inverse = {}

        # Сначала специальные токены
        for i, token in enumerate(self.special_tokens):
            self.vocab[i] = token
            self.vocab_inverse[token] = i

        # Затем все остальные токены в алфавитном порядке
        other_tokens = sorted(all_tokens - set(self.special_tokens))
        for token in other_tokens:
            if token not in self.vocab_inverse:
                idx = len(self.vocab)
                self.vocab[idx] = token
                self.vocab_inverse[token] = idx

        self.vocab_size = len(self.vocab)

    def encode(self, text: str) -> List[int]:
        """
        Кодирование текста в последовательность id.
        """
        words = self._get_words(text)
        token_ids = []

        for word in words:
            # Начальное представление слова как символов
            tokens = list(word) + ['</w>']

            # Применяем правила слияния в порядке их обучения
            for pair in self.merges:
                i = 0
                new_tokens = []

                while i < len(tokens):
                    if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == pair:
                        new_tokens.append(pair[0] + pair[1])
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1

                tokens = new_tokens

            # Конвертируем токены в id
            for token in tokens:
                if token in self.vocab_inverse:
                    token_ids.append(self.vocab_inverse[token])
                else:
                    # Если токен не найден, используем <unk>
                    token_ids.append(self.vocab_inverse['<unk>'])

        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        """
        Декодирование последовательности id обратно в текст.
        """
        # Конвертируем id в токены
        tokens = [self.vocab.get(token_id, '<unk>') for token_id in token_ids]

        # Склеиваем токены
        text = ''.join(tokens)

        # Восстанавливаем текст
        # Удаляем маркеры конца слова и восстанавливаем пробелы
        text = text.replace('</w>', ' ')

        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def save(self, filepath: str):
        """Сохранение токенизатора в файл."""
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            'vocab': self.vocab,
            'merges': self.merges,
            'vocab_size': self.vocab_size
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Токенизатор сохранен в {filepath}")

    def load(self, filepath: str):
        """Загрузка токенизатора из файла."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Преобразуем ключи vocab обратно в int
        self.vocab = {int(k): v for k, v in data['vocab'].items()}
        self.vocab_inverse = {v: k for k, v in self.vocab.items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.vocab_size = data['vocab_size']

        # Восстанавливаем merge_rules
        self.merge_rules = {}
        for pair in self.merges:
            self.merge_rules[pair] = pair[0] + pair[1]

        print(f"Токенизатор загружен из {filepath}")
        print(f"Размер словаря: {self.vocab_size}")

    def get_stats(self, corpus: List[str]) -> Dict:
        """
        Получение статистики по токенизации корпуса.
        """
        lengths = []

        for text in corpus:
            token_ids = self.encode(text)
            lengths.append(len(token_ids))

        if not lengths:
            # Если нет данных, возвращаем значения по умолчанию
            return {
                'vocab_size': self.vocab_size,
                'num_merges': len(self.merges),
                'avg_length': 0,
                'median_length': 0,
                'std_length': 0,
                'max_length': 0,
                'min_length': 0,
                'p95_length': 0,
                'p99_length': 0,
                'long_ratio': 0,
                'total_tokens': 0,
                'num_samples': 0
            }

        lengths = np.array(lengths)

        # Считаем процентили, только если есть достаточно данных
        if len(lengths) > 1:
            p99 = np.percentile(lengths, 99)
            long_ratio = np.mean(lengths > p99)
        else:
            # Если только один образец
            p99 = lengths[0]
            long_ratio = 0.0

        stats = {
            'vocab_size': self.vocab_size,
            'num_merges': len(self.merges),
            'avg_length': float(np.mean(lengths)),
            'median_length': float(np.median(lengths)),
            'std_length': float(np.std(lengths)) if len(lengths) > 1 else 0.0,
            'max_length': int(np.max(lengths)),
            'min_length': int(np.min(lengths)),
            'p95_length': float(np.percentile(lengths, 95)) if len(lengths) > 1 else float(lengths[0]),
            'p99_length': float(p99),
            'long_ratio': float(long_ratio),
            'total_tokens': int(np.sum(lengths)),
            'num_samples': len(lengths)
        }

        return stats