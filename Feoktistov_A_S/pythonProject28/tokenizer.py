import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import numpy as np


class BPETokenizer:
    def __init__(self, num_merges: int = 8000):
        """
        Инициализация BPE токенизатора.

        Args:
            num_merges: Количество слияний для обучения
        """
        self.vocab = {}  # id -> token
        self.token_to_id = {}  # token -> id
        self.merges = []  # список слияний (pair, new_token)
        self.num_merges = num_merges
        self.unk_token = "<UNK>"
        self.unk_id = None
        self.pad_token = "<PAD>"
        self.pad_id = None

    def train(self, corpus: List[str], num_merges: Optional[int] = None,
              verbose: bool = True) -> None:
        """
        Обучение BPE токенизатора на корпусе текстов.

        Args:
            corpus: Список текстов для обучения
            num_merges: Количество слияний (переопределяет self.num_merges)
            verbose: Вывод прогресса обучения
        """
        if num_merges is not None:
            self.num_merges = num_merges

        if verbose:
            print(f"Начало обучения BPE с {self.num_merges} слияниями...")
            print(f"Размер корпуса: {len(corpus)} документов")

        # 1. Препроцессинг текста
        if verbose:
            print("Препроцессинг текста...")

        # Разбиваем текст на слова с сохранением пробелов
        words = []
        word_freqs = Counter()

        for text in corpus:
            # Добавляем пробел в конец каждого слова для отслеживания границ слов
            processed_words = self._split_text_into_words(text)
            words.extend(processed_words)
            word_freqs.update(processed_words)

        if verbose:
            print(f"Найдено уникальных слов: {len(word_freqs)}")
            print(f"Всего слов: {len(words)}")

        # 2. Инициализация словаря символами
        chars = set()
        for word in word_freqs.keys():
            chars.update(word)

        # Сортируем символы для детерминированности
        sorted_chars = sorted(chars)

        # Инициализируем словарь
        self.vocab = {}
        for i, char in enumerate(sorted_chars):
            self.vocab[i] = char

        # Добавляем специальные токены
        self.unk_id = len(self.vocab)
        self.vocab[self.unk_id] = self.unk_token

        self.pad_id = len(self.vocab)
        self.vocab[self.pad_id] = self.pad_token

        # Создаем обратное отображение
        self._update_token_to_id()

        # 3. Преобразуем слова в последовательности символов
        if verbose:
            print("Подготовка данных для слияний...")

        # Создаем представление слов как списков символов
        word_representations = {}
        for word, freq in word_freqs.items():
            word_representations[word] = {
                'tokens': list(word),  # список символов
                'freq': freq
            }

        # 4. Итеративные слияния
        if verbose:
            print(f"Начало {self.num_merges} итераций слияний...")

        for i in range(self.num_merges):
            if verbose and i % 500 == 0:
                print(f"Слияние {i}/{self.num_merges}...")

            # Подсчитываем частоту пар
            pair_freqs = self._get_pair_frequencies(word_representations)

            if not pair_freqs:
                if verbose:
                    print(f"Больше нет пар для слияния на итерации {i}")
                break

            # Находим самую частую пару
            most_frequent_pair = max(pair_freqs.items(), key=lambda x: x[1])[0]

            # Создаем новый токен
            new_token = most_frequent_pair[0] + most_frequent_pair[1]
            new_id = len(self.vocab)
            self.vocab[new_id] = new_token
            self.merges.append((most_frequent_pair, new_token))

            # Обновляем обратное отображение
            self._update_token_to_id()

            # Применяем слияние ко всем словам
            self._apply_merge(word_representations, most_frequent_pair, new_token)

        if verbose:
            print(f"Обучение завершено!")
            print(f"Итоговый размер словаря: {len(self.vocab)} токенов")
            print(f"Выполнено слияний: {len(self.merges)}")

    def encode(self, text: str) -> List[int]:
        """
        Кодирование текста в последовательность id.

        Args:
            text: Входной текст

        Returns:
            Список id токенов
        """
        # Разбиваем текст на слова
        words = self._split_text_into_words(text)

        ids = []

        for word in words:
            # Начинаем с символов слова
            tokens = list(word)

            # Применяем все слияния в порядке их обучения
            for pair, new_token in self.merges:
                new_tokens = []
                i = 0

                while i < len(tokens):
                    # Если можем объединить текущий и следующий токен
                    if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                        new_tokens.append(new_token)
                        i += 2  # Пропускаем объединенную пару
                    else:
                        new_tokens.append(tokens[i])
                        i += 1

                tokens = new_tokens

            # Конвертируем токены в id
            for token in tokens:
                if token in self.token_to_id:
                    ids.append(self.token_to_id[token])
                else:
                    ids.append(self.unk_id)

        return ids

    def decode(self, ids: List[int]) -> str:
        """
        Декодирование последовательности id обратно в текст.

        Args:
            ids: Список id токенов

        Returns:
            Декодированный текст
        """
        tokens = []

        for id_ in ids:
            if id_ in self.vocab:
                tokens.append(self.vocab[id_])
            else:
                tokens.append(self.unk_token)

        # Собираем токены в строку
        result = ''.join(tokens)

        # Восстанавливаем пробелы (убираем специальный символ конца слова)
        result = result.replace('Ġ', ' ')

        return result

    def save(self, filepath: str) -> None:
        """
        Сохранение токенизатора в файл.

        Args:
            filepath: Путь для сохранения
        """
        data = {
            'vocab': self.vocab,
            'merges': self.merges,
            'num_merges': self.num_merges,
            'unk_token': self.unk_token,
            'unk_id': self.unk_id,
            'pad_token': self.pad_token,
            'pad_id': self.pad_id
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Токенизатор сохранен в {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'BPETokenizer':
        """
        Загрузка токенизатора из файла.

        Args:
            filepath: Путь к файлу с сохраненным токенизатором

        Returns:
            Загруженный токенизатор
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tokenizer = cls(num_merges=data['num_merges'])

        # Конвертируем ключи vocab в int
        tokenizer.vocab = {int(k): v for k, v in data['vocab'].items()}
        tokenizer.merges = data['merges']
        tokenizer.unk_token = data['unk_token']
        tokenizer.unk_id = data['unk_id']
        tokenizer.pad_token = data['pad_token']
        tokenizer.pad_id = data['pad_id']

        tokenizer._update_token_to_id()

        print(f"Токенизатор загружен из {filepath}")
        print(f"Размер словаря: {len(tokenizer.vocab)} токенов")

        return tokenizer

    def _split_text_into_words(self, text: str) -> List[str]:
        """
        Разбиение текста на слова с добавлением специального символа.

        Args:
            text: Входной текст

        Returns:
            Список слов с специальным символом
        """
        # Используем специальный символ для обозначения начала слова (кроме первого)
        # Вместо оригинального BPE, используем "Ġ" как в GPT-2
        words = []

        # Простой токенизатор на пробелах
        tokens = text.split()

        for i, token in enumerate(tokens):
            # Для первого слова не добавляем специальный символ
            if i == 0:
                words.append(token)
            else:
                words.append('Ġ' + token)

        return words

    def _update_token_to_id(self) -> None:
        """Обновление обратного отображения token->id."""
        self.token_to_id = {v: k for k, v in self.vocab.items()}

    def _get_pair_frequencies(self, word_representations: Dict) -> Dict[Tuple[str, str], int]:
        """
        Подсчет частот пар соседних токенов.

        Args:
            word_representations: Словарь представлений слов

        Returns:
            Словарь частот пар
        """
        pair_freqs = Counter()

        for word_data in word_representations.values():
            tokens = word_data['tokens']
            freq = word_data['freq']

            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                pair_freqs[pair] += freq

        return dict(pair_freqs)

    def _apply_merge(self, word_representations: Dict,
                     pair: Tuple[str, str], new_token: str) -> None:
        """
        Применение слияния ко всем словам.

        Args:
            word_representations: Словарь представлений слов
            pair: Пара для слияния
            new_token: Новый токен
        """
        for word, word_data in word_representations.items():
            tokens = word_data['tokens']
            new_tokens = []
            i = 0

            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                    new_tokens.append(new_token)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1

            word_representations[word]['tokens'] = new_tokens

    def get_vocab_size(self) -> int:
        """Получение размера словаря."""
        return len(self.vocab)

    def get_stats(self) -> Dict:
        """Получение статистики токенизатора."""
        return {
            'vocab_size': len(self.vocab),
            'num_merges': len(self.merges),
            'unk_id': self.unk_id,
            'pad_id': self.pad_id
        }