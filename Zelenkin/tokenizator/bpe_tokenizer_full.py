"""
BPE Tokenizer - полная реализация с нуля
Автор: AI Assistant
"""

import json
import re
import os
import sys
import time
import random
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

# Для прогресс-бара
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Заглушка для tqdm
    class tqdm:
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable
            self.disable = kwargs.get('disable', False)

        def __iter__(self):
            if self.iterable:
                return iter(self.iterable)
            return iter([])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def update(self, n=1):
            pass

        def set_description(self, desc=None):
            pass

# Для numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("ВНИМАНИЕ: numpy не установлен. Установите: pip install numpy")

    # Простая замена функций numpy
    class np:
        @staticmethod
        def mean(arr):
            return sum(arr) / len(arr) if arr else 0

        @staticmethod
        def median(arr):
            if not arr:
                return 0
            sorted_arr = sorted(arr)
            n = len(sorted_arr)
            mid = n // 2
            if n % 2 == 0:
                return (sorted_arr[mid - 1] + sorted_arr[mid]) / 2
            return sorted_arr[mid]

        @staticmethod
        def std(arr):
            if not arr or len(arr) < 2:
                return 0
            mean_val = sum(arr) / len(arr)
            variance = sum((x - mean_val) ** 2 for x in arr) / (len(arr) - 1)
            return variance ** 0.5

        @staticmethod
        def max(arr):
            return max(arr) if arr else 0

        @staticmethod
        def min(arr):
            return min(arr) if arr else 0

# ==================== УТИЛИТЫ ДЛЯ РАБОТЫ С ДАННЫМИ ====================

def read_corpus(filepath: str) -> List[str]:
    """
    Чтение текстового корпуса из файла.

    Args:
        filepath: Путь к файлу

    Returns:
        Список строк (абзацев/предложений)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines
    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
        return []
    except UnicodeDecodeError:
        print(f"Ошибка декодирования файла {filepath}. Убедитесь, что файл в кодировке UTF-8.")
        return []


def split_train_val(corpus: List[str], val_ratio: float = 0.1, seed: int = 42) -> Tuple[List[str], List[str]]:
    """
    Разделение корпуса на обучающую и валидационную части.

    Args:
        corpus: Исходный корпус
        val_ratio: Доля валидационных данных
        seed: Seed для воспроизводимости

    Returns:
        (train_corpus, val_corpus)
    """
    if not corpus:
        return [], []

    random.seed(seed)

    # Перемешиваем корпус
    shuffled_corpus = corpus.copy()
    random.shuffle(shuffled_corpus)

    # Разделяем
    split_idx = int(len(shuffled_corpus) * (1 - val_ratio))
    train_corpus = shuffled_corpus[:split_idx]
    val_corpus = shuffled_corpus[split_idx:]

    return train_corpus, val_corpus


def preprocess_text(text: str) -> str:
    """
    Базовая предобработка текста.

    Args:
        text: Исходный текст

    Returns:
        Обработанный текст
    """
    # Нормализация пробелов
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==================== ОСНОВНОЙ КЛАСС BPE ТОКЕНИЗАТОРА ====================

class BPETokenizer:
    def __init__(self, vocab_size: Optional[int] = None, num_merges: Optional[int] = None):
        """
        Инициализация BPE токенизатора.

        Args:
            vocab_size: Максимальный размер словаря (используется если num_merges не указан)
            num_merges: Количество операций слияния (приоритет над vocab_size)
        """
        self.vocab = {}  # token -> id
        self.id_to_token = {}  # id -> token
        self.merges = {}  # (token1, token2) -> merged_token
        # Упрощенный паттерн для токенизации (без \p{} который требует библиотеки regex)
        self.pattern = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[^\s]+|\s+(?!\S)|\s+""")
        self.unk_token = "<unk>"
        self.pad_token = "<pad>"
        self.bos_token = "<bos>"
        self.eos_token = "<eos>"

        # Для обратного отслеживания слияний
        self.merge_history = []  # Список выполненных слияний

        # Если задан vocab_size, вычисляем num_merges
        if vocab_size is not None and num_merges is None:
            # Базовый словарь: специальные токены + символы
            base_vocab = 4  # специальные токены
            num_merges = vocab_size - base_vocab

    def train(self, corpus: List[str], num_merges: int = 1000, verbose: bool = True):
        """
        Обучение BPE на корпусе текста.

        Args:
            corpus: Список строк для обучения
            num_merges: Количество операций слияния
            verbose: Вывод прогресса
        """
        if not corpus:
            print("Корпус пуст. Обучение невозможно.")
            return

        # 1. Предварительная токенизация на слова
        words = []
        word_frequencies = Counter()

        for text in corpus:
            # Простая токенизация по пробелам и знакам пунктуации
            # Сохраняем пробелы как отдельные токены
            tokens = []
            current_token = ""

            for char in text:
                if char.isspace():
                    if current_token:
                        tokens.append(current_token)
                        current_token = ""
                    tokens.append(" ")  # Пробел как отдельный токен
                else:
                    current_token += char

            if current_token:
                tokens.append(current_token)

            words.extend(tokens)
            word_frequencies.update([tuple(tokens)])

        if not words:
            print("Нет слов для обучения.")
            return

        # 2. Инициализация словаря символов
        # Сначала добавляем специальные токены
        special_tokens = [self.unk_token, self.pad_token, self.bos_token, self.eos_token]
        for token in special_tokens:
            if token not in self.vocab:
                id_ = len(self.vocab)
                self.vocab[token] = id_
                self.id_to_token[id_] = token

        # Собираем все уникальные символы
        characters = set()
        for word in words:
            if word != " ":  # Пробел уже добавлен как специальный токен
                characters.update(word)

        # Добавляем символы в словарь
        for char in sorted(characters):
            if char not in self.vocab:
                id_ = len(self.vocab)
                self.vocab[char] = id_
                self.id_to_token[id_] = char

        # Также добавляем пробел, если его еще нет
        if " " not in self.vocab:
            space_id = len(self.vocab)
            self.vocab[" "] = space_id
            self.id_to_token[space_id] = " "

        # 3. Инициализация токенов для каждого слова
        # Представляем каждое слово как список символов
        word_tokenizations = {}
        for word_tuple, freq in word_frequencies.items():
            word = ''.join(word_tuple)
            # Инициализируем как список символов
            tokens = []
            for char in word:
                tokens.append(char)
            word_tokenizations[word] = {
                'tokens': tokens,
                'frequency': freq
            }

        # 4. Итеративные слияния
        if verbose:
            print(f"Начальный размер словаря: {len(self.vocab)}")
            print(f"Выполняем {num_merges} слияний...")

        # Используем tqdm для прогресс-бара, если доступен
        iterator = range(num_merges)
        if HAS_TQDM and verbose:
            iterator = tqdm(iterator, desc="Обучение BPE")

        merges_done = 0
        for merge_step in iterator:
            # Подсчет частот пар
            pair_frequencies = Counter()

            for word_data in word_tokenizations.values():
                tokens = word_data['tokens']
                freq = word_data['frequency']

                # Подсчитываем пары соседних токенов
                for i in range(len(tokens) - 1):
                    pair = (tokens[i], tokens[i + 1])
                    pair_frequencies[pair] += freq

            if not pair_frequencies:
                if verbose:
                    print(f"Нет больше пар для слияния на шаге {merge_step}")
                break

            # Находим самую частую пару
            most_common_pair, max_freq = pair_frequencies.most_common(1)[0]

            if max_freq < 2:  # Минимум 2 вхождения для слияния
                if verbose:
                    print(f"Слишком низкая частота на шаге {merge_step}")
                break

            # Создаем новый токен
            new_token = most_common_pair[0] + most_common_pair[1]

            # Добавляем в словарь
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token

            # Сохраняем правило слияния
            self.merges[most_common_pair] = new_token
            self.merge_history.append(most_common_pair)

            # Обновляем все слова
            for word, word_data in word_tokenizations.items():
                tokens = word_data['tokens']
                new_tokens = []
                i = 0

                while i < len(tokens):
                    if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == most_common_pair:
                        new_tokens.append(new_token)
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1

                word_tokenizations[word]['tokens'] = new_tokens

            merges_done += 1

        if verbose:
            print(f"Конечный размер словаря: {len(self.vocab)}")
            print(f"Выполнено слияний: {merges_done} из запланированных {num_merges}")

    def encode(self, text: str) -> List[int]:
        """
        Кодирование текста в последовательность id.

        Args:
            text: Входной текст

        Returns:
            Список id токенов
        """
        if not text:
            return []

        # 1. Разбиваем текст на слова и пробелы
        # Используем простую логику: разделяем по пробелам, но сохраняем пробелы
        tokens = []
        current_token = ""

        for char in text:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(" ")  # Пробел как отдельный токен
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        # 2. Кодируем каждый токен отдельно
        token_ids = []

        for token in tokens:
            if token == " ":
                # Для пробелов используем токен пробела
                if " " in self.vocab:
                    token_ids.append(self.vocab[" "])
                continue

            # Инициализируем как список символов
            sub_tokens = list(token)

            # Применяем слияния
            while True:
                # Находим пару с наивысшим приоритетом (первое в истории слияний)
                best_pair = None
                best_idx = -1

                for i in range(len(sub_tokens) - 1):
                    pair = (sub_tokens[i], sub_tokens[i + 1])
                    if pair in self.merges:
                        # Находим индекс в истории слияний
                        try:
                            idx = self.merge_history.index(pair)
                            if best_idx == -1 or idx < best_idx:
                                best_idx = idx
                                best_pair = pair
                        except ValueError:
                            continue

                if best_pair is None:
                    break

                # Выполняем слияние
                new_token = self.merges[best_pair]
                new_sub_tokens = []
                i = 0

                while i < len(sub_tokens):
                    if i < len(sub_tokens) - 1 and (sub_tokens[i], sub_tokens[i + 1]) == best_pair:
                        new_sub_tokens.append(new_token)
                        i += 2
                    else:
                        new_sub_tokens.append(sub_tokens[i])
                        i += 1

                sub_tokens = new_sub_tokens

            # Конвертируем токены в id
            for sub_token in sub_tokens:
                if sub_token in self.vocab:
                    token_ids.append(self.vocab[sub_token])
                else:
                    # Для неизвестных токенов используем UNK
                    if self.unk_token in self.vocab:
                        token_ids.append(self.vocab[self.unk_token])
                    else:
                        # Если даже UNK нет, добавляем 0 (первый токен)
                        token_ids.append(0)

        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        """
        Декодирование последовательности id обратно в текст.

        Args:
            token_ids: Список id токенов

        Returns:
            Восстановленный текст
        """
        if not token_ids:
            return ""

        # Конвертируем id в токены
        tokens = []
        for token_id in token_ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append(self.unk_token)

        # Объединяем токены
        text = ""
        for i, token in enumerate(tokens):
            # Если текущий токен - пробел, просто добавляем его
            if token == " ":
                text += " "
            # Если следующий токен не пробел и текущий не пробел, добавляем как есть
            elif i < len(tokens) - 1 and tokens[i + 1] != " " and not tokens[i + 1].startswith(" ") and token != " ":
                text += token
            # Иначе добавляем токен и пробел после него (если нужно)
            else:
                text += token

        # Восстанавливаем пробелы между словами
        # Убираем лишние пробелы, которые могли появиться
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def save(self, filepath: str):
        """
        Сохранение токенизатора в файл.

        Args:
            filepath: Путь для сохранения
        """
        # Конвертируем ключи merges в строки для JSON
        merges_list = []
        for pair, merged in self.merges.items():
            merges_list.append([list(pair), merged])

        data = {
            'vocab': self.vocab,
            'id_to_token': {str(k): v for k, v in self.id_to_token.items()},
            'merges': merges_list,
            'merge_history': [[list(pair[0]), list(pair[1])] if isinstance(pair[0], tuple) else list(pair) for pair in self.merge_history],
            'special_tokens': {
                'unk': self.unk_token,
                'pad': self.pad_token,
                'bos': self.bos_token,
                'eos': self.eos_token
            }
        }

        # Создаем директорию, если нужно
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str):
        """
        Загрузка токенизатора из файла.

        Args:
            filepath: Путь к файлу
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.vocab = {k: int(v) if isinstance(v, str) else v for k, v in data['vocab'].items()}
        self.id_to_token = {int(k): v for k, v in data['id_to_token'].items()}

        # Восстанавливаем merges
        self.merges = {}
        for item in data['merges']:
            pair = tuple(item[0])
            self.merges[pair] = item[1]

        # Восстанавливаем merge_history
        self.merge_history = []
        for item in data['merge_history']:
            if isinstance(item[0], list):
                self.merge_history.append((item[0][0], item[0][1]))
            else:
                self.merge_history.append((item[0], item[1]))

        special_tokens = data['special_tokens']
        self.unk_token = special_tokens['unk']
        self.pad_token = special_tokens['pad']
        self.bos_token = special_tokens['bos']
        self.eos_token = special_tokens['eos']

    def get_vocab_size(self) -> int:
        """Возвращает размер словаря."""
        return len(self.vocab)

    def tokenize(self, text: str) -> List[str]:
        """
        Токенизация текста (возвращает строки токенов).

        Args:
            text: Входной текст

        Returns:
            Список токенов как строк
        """
        token_ids = self.encode(text)
        return [self.id_to_token.get(token_id, self.unk_token) for token_id in token_ids]

    def print_vocab_sample(self, n: int = 20):
        """Печатает первые n токенов из словаря."""
        vocab_size = self.get_vocab_size()
        print(f"Размер словаря: {vocab_size}")
        if vocab_size > 0:
            print("Первые 20 токенов:")
            items = list(self.vocab.items())
            for i in range(min(n, len(items))):
                token, token_id = items[i]
                print(f"  {token_id:4d}: '{token}'")


# ==================== МЕТРИКИ И АНАЛИЗ ====================

def calculate_sequence_lengths(tokenizer: BPETokenizer, corpus: List[str]) -> List[int]:
    """
    Вычисление длин последовательностей токенов.

    Args:
        tokenizer: Обученный токенизатор
        corpus: Корпус текстов

    Returns:
        Список длин последовательностей
    """
    lengths = []
    for text in corpus:
        token_ids = tokenizer.encode(text)
        lengths.append(len(token_ids))

    return lengths


def analyze_tokenizations(tokenizer: BPETokenizer, corpus: List[str]) -> dict:
    """
    Анализ токенизаций на корпусе.

    Args:
        tokenizer: Обученный токенизатор
        corpus: Корпус текстов

    Returns:
        Словарь с метриками
    """
    if not corpus:
        return {
            'avg_length': 0,
            'max_length': 0,
            'min_length': 0,
            'median_length': 0,
            'std_length': 0,
            'total_tokens': 0,
            'total_sequences': 0,
            'threshold_99': 0,
            'long_sequences_percentage': 0,
            'vocab_size': tokenizer.get_vocab_size()
        }

    lengths = calculate_sequence_lengths(tokenizer, corpus)

    # Сортируем длины для вычисления процентилей
    sorted_lengths = sorted(lengths)

    # Вычисляем 99-й процентиль (top-1% самых длинных)
    idx_99 = int(len(sorted_lengths) * 0.99)
    threshold_99 = sorted_lengths[idx_99] if idx_99 < len(sorted_lengths) else sorted_lengths[-1]

    # Доля очень длинных последовательностей (длиннее 99-го процентиля)
    long_sequences = sum(1 for length in lengths if length > threshold_99)
    long_percentage = long_sequences / len(lengths) if lengths else 0

    return {
        'avg_length': float(np.mean(lengths)),
        'max_length': float(np.max(lengths)),
        'min_length': float(np.min(lengths)),
        'median_length': float(np.median(lengths)),
        'std_length': float(np.std(lengths)),
        'total_tokens': sum(lengths),
        'total_sequences': len(lengths),
        'threshold_99': threshold_99,
        'long_sequences_percentage': long_percentage,
        'vocab_size': tokenizer.get_vocab_size()
    }


# ==================== ЭКСПЕРИМЕНТЫ ====================

def run_experiment(data_path: str, num_merges_list: List[int], val_ratio: float = 0.1):
    """
    Запуск эксперимента с разными значениями num_merges.

    Args:
        data_path: Путь к файлу с данными
        num_merges_list: Список значений num_merges для тестирования
        val_ratio: Доля валидационных данных
    """
    print("=" * 60)
    print("BPE Tokenizer Experiment")
    print("=" * 60)

    # 1. Чтение и подготовка данных
    print("\n1. Загрузка данных...")
    corpus = read_corpus(data_path)

    if not corpus:
        print(f"Файл {data_path} пуст или не найден. Создаю демонстрационный корпус...")
        # Создаем демонстрационный корпус
        corpus = [
            "Это пример текста на русском языке.",
            "Here is some text in English.",
            "BPE токенизация - это полезная техника для NLP.",
            "Byte Pair Encoding helps with rare words.",
            "Привет мир! Hello world!",
            "Машинное обучение и обработка естественного языка.",
            "Natural Language Processing with BPE tokenization.",
            "The quick brown fox jumps over the lazy dog.",
            "Съешь же ещё этих мягких французских булок, да выпей чаю."
        ]

        # Сохраняем демонстрационный корпус
        with open('demo_data.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(corpus))
        print("Демонстрационный корпус создан: 'demo_data.txt'")
        data_path = 'demo_data.txt'

    print(f"   Всего строк: {len(corpus)}")

    # Предобработка
    corpus = [preprocess_text(text) for text in corpus]

    # Разделение на train/val
    train_corpus, val_corpus = split_train_val(corpus, val_ratio=val_ratio)
    print(f"   Обучающая выборка: {len(train_corpus)} строк")
    print(f"   Валидационная выборка: {len(val_corpus)} строк")

    # 2. Эксперимент с разными num_merges
    results = []

    for num_merges in num_merges_list:
        print(f"\n{'='*40}")
        print(f"Эксперимент: num_merges = {num_merges}")
        print(f"{'='*40}")

        # Создаем и обучаем токенизатор
        tokenizer = BPETokenizer()

        start_time = time.time()
        tokenizer.train(train_corpus, num_merges=num_merges, verbose=True)
        training_time = time.time() - start_time

        print(f"Время обучения: {training_time:.2f} секунд")
        tokenizer.print_vocab_sample()

        # Анализируем на валидационной выборке
        metrics = analyze_tokenizations(tokenizer, val_corpus)

        print(f"\nМетрики на валидационной выборке:")
        print(f"  Средняя длина последовательности: {metrics['avg_length']:.2f}")
        print(f"  Максимальная длина: {metrics['max_length']}")
        print(f"  Минимальная длина: {metrics['min_length']}")
        print(f"  Медианная длина: {metrics['median_length']:.2f}")
        print(f"  Стандартное отклонение: {metrics['std_length']:.2f}")
        print(f"  Порог 99-го процентиля: {metrics['threshold_99']}")
        print(f"  Доля очень длинных последовательностей: {metrics['long_sequences_percentage']:.2%}")

        # Проверяем корректность decode(encode(text)) == text
        print("\nПроверка корректности decode(encode(text))...")
        correct = 0
        total = min(100, len(val_corpus))  # Проверяем на первых 100 примерах или меньше

        test_texts = val_corpus[:total]
        for text in test_texts:
            try:
                encoded = tokenizer.encode(text)
                decoded = tokenizer.decode(encoded)
                if decoded == text:
                    correct += 1
                else:
                    # Для отладки можно раскомментировать:
                    # print(f"Ошибка: '{text}' -> '{decoded}'")
                    pass
            except Exception as e:
                print(f"Ошибка при обработке текста: {e}")

        accuracy = correct / total if total > 0 else 0
        print(f"Точность восстановления: {accuracy:.4f} ({correct}/{total})")

        # Тестируем на нескольких примерах
        print("\nПримеры токенизации:")
        test_examples = [
            "Привет мир!",
            "Hello world!",
            "BPE токенизация",
            "Natural Language Processing"
        ]

        for example in test_examples[:3]:
            token_ids = tokenizer.encode(example)
            tokens = tokenizer.tokenize(example)
            decoded = tokenizer.decode(token_ids)
            print(f"  '{example}' -> {tokens} (ids: {token_ids}) -> '{decoded}'")

        # Сохраняем результаты
        result = {
            'num_merges': num_merges,
            'training_time': training_time,
            'vocab_size': tokenizer.get_vocab_size(),
            'metrics': metrics,
            'reconstruction_accuracy': accuracy
        }
        results.append(result)

        # Сохраняем токенизатор
        if num_merges > 0:
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / f"bpe_tokenizer_{num_merges}.json"
            tokenizer.save(str(model_path))
            print(f"\nТокенизатор сохранен: {model_path}")

    # 3. Вывод результатов сравнения
    print(f"\n{'='*60}")
    print("Сводка результатов")
    print(f"{'='*60}")

    headers = ["num_merges", "vocab_size", "avg_len", "training_time", "accuracy"]
    print(f"{headers[0]:>12} {headers[1]:>12} {headers[2]:>12} {headers[3]:>12} {headers[4]:>12}")
    print("-" * 60)

    for result in results:
        print(f"{result['num_merges']:>12} "
              f"{result['vocab_size']:>12} "
              f"{result['metrics']['avg_length']:>12.2f} "
              f"{result['training_time']:>12.2f} "
              f"{result['reconstruction_accuracy']:>12.4f}")

    # 4. Визуализация (опционально)
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # График 1: Средняя длина vs num_merges
        x = [r['num_merges'] for r in results]
        y_avg_len = [r['metrics']['avg_length'] for r in results]

        axes[0].plot(x, y_avg_len, 'bo-', linewidth=2, markersize=8)
        axes[0].set_xlabel('num_merges')
        axes[0].set_ylabel('Средняя длина последовательности')
        axes[0].set_title('Зависимость средней длины от num_merges')
        axes[0].grid(True, alpha=0.3)

        # График 2: Размер словаря vs num_merges
        y_vocab_size = [r['vocab_size'] for r in results]

        axes[1].plot(x, y_vocab_size, 'ro-', linewidth=2, markersize=8)
        axes[1].set_xlabel('num_merges')
        axes[1].set_ylabel('Размер словаря')
        axes[1].set_title('Зависимость размера словаря от num_merges')
        axes[1].grid(True, alpha=0.3)

        # График 3: Точность восстановления vs num_merges
        y_accuracy = [r['reconstruction_accuracy'] for r in results]

        axes[2].plot(x, y_accuracy, 'go-', linewidth=2, markersize=8)
        axes[2].set_xlabel('num_merges')
        axes[2].set_ylabel('Точность восстановления')
        axes[2].set_title('Точность восстановления от num_merges')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('bpe_experiment_results.png', dpi=150, bbox_inches='tight')
        print("\nГрафики сохранены в 'bpe_experiment_results.png'")

        # Показываем график только если не в CI/CD среде
        if 'CI' not in os.environ:
            plt.show()

    except ImportError:
        print("\nMatplotlib не установлен, визуализация пропущена.")
        print("Установите: pip install matplotlib")

    return results


def test_tokenizer_interactively(tokenizer_path: str = None):
    """
    Интерактивное тестирование токенизатора.

    Args:
        tokenizer_path: Путь к сохраненному токенизатору (опционально)
    """
    if tokenizer_path and os.path.exists(tokenizer_path):
        tokenizer = BPETokenizer()
        tokenizer.load(tokenizer_path)
        print(f"Загружен токенизатор с vocab_size={tokenizer.get_vocab_size()}")
        tokenizer.print_vocab_sample()
    else:
        # Создаем простой токенизатор для демонстрации
        print("Создаю демонстрационный токенизатор...")
        tokenizer = BPETokenizer()
        corpus = ["Hello world!", "This is a test.", "Привет мир!", "BPE tokenization test."]
        tokenizer.train(corpus, num_merges=20, verbose=False)
        print(f"Создан токенизатор с vocab_size={tokenizer.get_vocab_size()}")

    print("\n" + "="*60)
    print("Интерактивное тестирование токенизатора")
    print("Введите текст для токенизации (или 'quit' для выхода):")
    print("="*60)

    while True:
        try:
            text = input("\nВвод: ").strip()
            if text.lower() == 'quit':
                break

            if not text:
                continue

            # Токенизация
            token_ids = tokenizer.encode(text)
            tokens = tokenizer.tokenize(text)
            decoded = tokenizer.decode(token_ids)

            print(f"\nИсходный текст: '{text}'")
            print(f"Токены ({len(tokens)}): {tokens}")
            print(f"ID токенов: {token_ids}")
            print(f"Декодированный текст: '{decoded}'")
            print(f"Корректность: {decoded == text}")

        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")


# ==================== ТЕСТЫ ====================

def run_tests():
    """Запуск встроенных тестов."""
    print("Запуск тестов BPE токенизатора...")

    # Создаем тестовый токенизатор
    tokenizer = BPETokenizer()
    test_corpus = [
        "hello world",
        "hello there",
        "world of tokens",
        "test tokenization",
        "привет мир",
        "тест токенизации"
    ]

    print("1. Обучение токенизатора...")
    tokenizer.train(test_corpus, num_merges=50, verbose=False)

    print(f"2. Размер словаря: {tokenizer.get_vocab_size()}")

    print("3. Тест encode/decode...")
    test_cases = [
        "hello world",
        "test tokenization",
        "привет мир",
        "",
        "hello world! test?"
    ]

    all_passed = True
    for text in test_cases:
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        passed = decoded == text
        all_passed = all_passed and passed

        status = "✓" if passed else "✗"
        print(f"  {status} '{text}' -> '{decoded}'")

    print("4. Тест сохранения и загрузки...")
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        # Сохраняем
        tokenizer.save(temp_path)

        # Загружаем
        new_tokenizer = BPETokenizer()
        new_tokenizer.load(temp_path)

        # Сравниваем
        test_text = "hello world test"
        encoded1 = tokenizer.encode(test_text)
        encoded2 = new_tokenizer.encode(test_text)

        if encoded1 == encoded2:
            print("  ✓ Сохранение и загрузка работают корректно")
        else:
            print("  ✗ Ошибка при сохранении/загрузке")
            all_passed = False
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    if all_passed:
        print("\nВсе тесты пройдены успешно! ✓")
    else:
        print("\nНекоторые тесты не пройдены! ✗")

    return all_passed


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():
    """Главная функция для запуска из командной строки."""
    parser = argparse.ArgumentParser(
        description='BPE Tokenizer Implementation - полная реализация с нуля',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python %(prog)s --mode experiment
  python %(prog)s --mode experiment --num_merges 0 500 2000
  python %(prog)s --mode train --train_merges 1000 --save_model my_tokenizer.json
  python %(prog)s --mode test --load_model models/bpe_tokenizer_1000.json
  python %(prog)s --mode run_tests
        """
    )

    parser.add_argument('--data', type=str, default='data.txt',
                       help='Путь к файлу с данными (по умолчанию: data.txt)')

    parser.add_argument('--mode', type=str, default='experiment',
                       choices=['experiment', 'test', 'train', 'run_tests'],
                       help='Режим работы: experiment, test, train, run_tests')

    parser.add_argument('--num_merges', type=int, nargs='+',
                       default=[0, 500, 2000, 8000],
                       help='Список значений num_merges для эксперимента (по умолчанию: 0 500 2000 8000)')

    parser.add_argument('--load_model', type=str,
                       help='Путь для загрузки обученной модели')

    parser.add_argument('--save_model', type=str,
                       help='Путь для сохранения обученной модели (для режима train)')

    parser.add_argument('--val_ratio', type=float, default=0.1,
                       help='Доля валидационных данных (по умолчанию: 0.1)')

    parser.add_argument('--train_merges', type=int, default=1000,
                       help='Количество слияний для режима train (по умолчанию: 1000)')

    args = parser.parse_args()

    # Проверяем наличие data.txt
    if args.mode in ['experiment', 'train'] and not os.path.exists(args.data):
        print(f"Файл данных '{args.data}' не найден.")
        print("Создаю демонстрационный корпус...")

        demo_corpus = [
            "Это пример текста на русском языке.",
            "Here is some text in English.",
            "BPE токенизация - это полезная техника для NLP.",
            "Byte Pair Encoding helps with rare words.",
            "Привет мир! Hello world!",
            "Машинное обучение и обработка естественного языка.",
            "Natural Language Processing with BPE tokenization.",
            "The quick brown fox jumps over the lazy dog.",
            "Съешь же ещё этих мягких французских булок, да выпей чаю."
        ]

        with open('demo_data.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(demo_corpus))

        print("Демонстрационный корпус создан: 'demo_data.txt'")
        args.data = 'demo_data.txt'

    if args.mode == 'experiment':
        run_experiment(args.data, args.num_merges, args.val_ratio)

    elif args.mode == 'test':
        test_tokenizer_interactively(args.load_model)

    elif args.mode == 'train':
        # Простое обучение и сохранение
        corpus = read_corpus(args.data)
        if not corpus:
            print(f"Файл {args.data} пуст или не найден.")
            return

        corpus = [preprocess_text(text) for text in corpus]

        num_merges = args.train_merges
        print(f"Обучение токенизатора с num_merges={num_merges}...")

        tokenizer = BPETokenizer()
        tokenizer.train(corpus, num_merges=num_merges, verbose=True)

        # Сохранение
        if args.save_model:
            model_path = args.save_model
        else:
            model_path = f'bpe_tokenizer_{num_merges}.json'

        tokenizer.save(model_path)
        print(f"Токенизатор сохранен в '{model_path}'")

        # Тест
        print("\nТестирование токенизатора:")
        test_texts = [
            "Пример текста для тестирования.",
            "Hello world!",
            "BPE токенизация работает!"
        ]

        for test_text in test_texts:
            encoded = tokenizer.encode(test_text)
            decoded = tokenizer.decode(encoded)

            print(f"\nИсходный: '{test_text}'")
            print(f"Токены: {tokenizer.tokenize(test_text)}")
            print(f"Декодированный: '{decoded}'")
            print(f"Корректность: {decoded == test_text}")

    elif args.mode == 'run_tests':
        run_tests()


# ==================== ЗАПУСК ПРОГРАММЫ ====================

if __name__ == "__main__":
    main()