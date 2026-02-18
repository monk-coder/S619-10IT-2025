import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set, Any
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

        # 1. Подготовка данных
        word_freqs = self._prepare_word_frequencies(corpus, verbose)

        # 2. Инициализация словаря символами
        self._initialize_vocab_from_words(word_freqs, verbose)

        # 3. Создание представлений слов
        word_representations = self._create_word_representations(word_freqs, verbose)

        # 4. Выполнение слияний BPE
        self._perform_bpe_merges(word_representations, verbose)

        # 5. Финальная статистика
        if verbose:
            self._print_training_summary()

    def _prepare_word_frequencies(self, corpus: List[str], verbose: bool) -> Dict[str, int]:
        """
        Подготовка частот слов из корпуса.

        Args:
            corpus: Корпус текстов
            verbose: Флаг вывода информации

        Returns:
            Dict[str, int]: Словарь частот слов
        """
        if verbose:
            print("Подготовка частот слов...")

        word_freqs = Counter()

        for text in corpus:
            processed_words = self._split_text_into_words(text)
            word_freqs.update(processed_words)

        if verbose:
            print(f"  Найдено уникальных слов: {len(word_freqs)}")
            print(f"  Всего слов: {sum(word_freqs.values())}")

        return dict(word_freqs)

    def _initialize_vocab_from_words(self, word_freqs: Dict[str, int], verbose: bool) -> None:
        """
        Инициализация словаря символами из слов.

        Args:
            word_freqs: Словарь частот слов
            verbose: Флаг вывода информации
        """
        if verbose:
            print("Инициализация словаря символами...")

        # Собираем все уникальные символы
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

        if verbose:
            print(f"  Найдено уникальных символов: {len(sorted_chars)}")
            print(f"  Начальный размер словаря: {len(self.vocab)}")

    def _create_word_representations(self, word_freqs: Dict[str, int],
                                     verbose: bool) -> Dict[str, Dict]:
        """
        Создание представлений слов как списков символов.

        Args:
            word_freqs: Словарь частот слов
            verbose: Флаг вывода информации

        Returns:
            Dict[str, Dict]: Представления слов
        """
        if verbose:
            print("Создание представлений слов...")

        word_representations = {}

        for word, freq in word_freqs.items():
            word_representations[word] = {
                'tokens': list(word),  # список символов
                'freq': freq
            }

        return word_representations

    def _perform_bpe_merges(self, word_representations: Dict[str, Dict],
                            verbose: bool) -> None:
        """
        Выполнение итеративных слияний BPE.

        Args:
            word_representations: Представления слов
            verbose: Флаг вывода информации
        """
        if verbose:
            print(f"Выполнение {self.num_merges} слияний BPE...")

        for i in range(self.num_merges):
            if verbose and self._should_print_progress(i):
                print(f"  Слияние {i}/{self.num_merges}...")

            # Находим самую частую пару
            most_frequent_pair = self._find_most_frequent_pair(word_representations)

            if most_frequent_pair is None:
                if verbose:
                    print(f"  Больше нет пар для слияния на итерации {i}")
                break

            # Создаем новый токен
            new_token = self._create_new_token(most_frequent_pair)

            # Сохраняем правило слияния
            self._add_merge_rule(most_frequent_pair, new_token)

            # Применяем слияние ко всем словам
            self._apply_merge_to_all_words(word_representations, most_frequent_pair, new_token)

    def _should_print_progress(self, iteration: int) -> bool:
        """
        Определение, нужно ли выводить прогресс на данной итерации.

        Args:
            iteration: Номер итерации

        Returns:
            bool: True если нужно вывести прогресс
        """
        if self.num_merges <= 100:
            return iteration % 10 == 0
        elif self.num_merges <= 1000:
            return iteration % 100 == 0
        else:
            return iteration % 500 == 0

    def _find_most_frequent_pair(self, word_representations: Dict[str, Dict]) -> Optional[Tuple[str, str]]:
        """
        Поиск самой частой пары токенов.

        Args:
            word_representations: Представления слов

        Returns:
            Optional[Tuple[str, str]]: Самая частая пара или None
        """
        pair_freqs = self._count_pair_frequencies(word_representations)

        if not pair_freqs:
            return None

        return max(pair_freqs.items(), key=lambda x: x[1])[0]

    def _count_pair_frequencies(self, word_representations: Dict[str, Dict]) -> Dict[Tuple[str, str], int]:
        """
        Подсчет частот всех пар токенов.

        Args:
            word_representations: Представления слов

        Returns:
            Dict[Tuple[str, str], int]: Частоты пар
        """
        pair_freqs = Counter()

        for word_data in word_representations.values():
            tokens = word_data['tokens']
            freq = word_data['freq']

            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                pair_freqs[pair] += freq

        return dict(pair_freqs)

    def _create_new_token(self, pair: Tuple[str, str]) -> str:
        """
        Создание нового токена из пары.

        Args:
            pair: Пара токенов

        Returns:
            str: Новый токен
        """
        return pair[0] + pair[1]

    def _add_merge_rule(self, pair: Tuple[str, str], new_token: str) -> None:
        """
        Добавление правила слияния и обновление словаря.

        Args:
            pair: Пара токенов
            new_token: Новый токен
        """
        # Добавляем новое правило слияния
        self.merges.append((pair, new_token))

        # Добавляем новый токен в словарь
        new_id = len(self.vocab)
        self.vocab[new_id] = new_token

        # Обновляем обратное отображение
        self._update_token_to_id()

    def _apply_merge_to_all_words(self, word_representations: Dict[str, Dict],
                                  pair: Tuple[str, str], new_token: str) -> None:
        """
        Применение слияния ко всем словам.

        Args:
            word_representations: Представления слов
            pair: Пара для слияния
            new_token: Новый токен
        """
        for word, word_data in word_representations.items():
            new_tokens = self._apply_merge_to_word(word_data['tokens'], pair, new_token)
            word_representations[word]['tokens'] = new_tokens

    def _apply_merge_to_word(self, tokens: List[str], pair: Tuple[str, str],
                             new_token: str) -> List[str]:
        """
        Применение слияния к одному слову.

        Args:
            tokens: Список токенов слова
            pair: Пара для слияния
            new_token: Новый токен

        Returns:
            List[str]: Обновленный список токенов
        """
        new_tokens = []
        i = 0

        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1

        return new_tokens

    def _print_training_summary(self) -> None:
        """Вывод итоговой статистики обучения."""
        print(f"\nОбучение завершено!")
        print(f"  Итоговый размер словаря: {len(self.vocab)} токенов")
        print(f"  Выполнено слияний: {len(self.merges)}")

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
            tokens = self._apply_all_merges(tokens)

            # Конвертируем токены в id
            word_ids = self._tokens_to_ids(tokens)
            ids.extend(word_ids)

        return ids

    def _apply_all_merges(self, tokens: List[str]) -> List[str]:
        """
        Применение всех правил слияния к списку токенов.

        Args:
            tokens: Исходный список токенов

        Returns:
            List[str]: Токены после всех слияний
        """
        for pair, new_token in self.merges:
            tokens = self._apply_single_merge(tokens, pair, new_token)

        return tokens

    def _apply_single_merge(self, tokens: List[str], pair: Tuple[str, str],
                            new_token: str) -> List[str]:
        """
        Применение одного правила слияния.

        Args:
            tokens: Список токенов
            pair: Пара для слияния
            new_token: Новый токен

        Returns:
            List[str]: Обновленный список токенов
        """
        new_tokens = []
        i = 0

        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1

        return new_tokens

    def _tokens_to_ids(self, tokens: List[str]) -> List[int]:
        """
        Преобразование списка токенов в список id.

        Args:
            tokens: Список токенов

        Returns:
            List[int]: Список id
        """
        ids = []

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
        # Преобразуем id в токены
        tokens = self._ids_to_tokens(ids)

        # Собираем токены в строку
        result = ''.join(tokens)

        # Восстанавливаем пробелы
        result = self._restore_spaces(result)

        return result

    def _ids_to_tokens(self, ids: List[int]) -> List[str]:
        """
        Преобразование списка id в список токенов.

        Args:
            ids: Список id

        Returns:
            List[str]: Список токенов
        """
        tokens = []

        for id_ in ids:
            if id_ in self.vocab:
                tokens.append(self.vocab[id_])
            else:
                tokens.append(self.unk_token)

        return tokens

    def _restore_spaces(self, text: str) -> str:
        """
        Восстановление пробелов в декодированном тексте.

        Args:
            text: Текст со специальными символами

        Returns:
            str: Текст с восстановленными пробелами
        """
        return text.replace('Ġ', ' ')

    def save(self, filepath: str) -> None:
        """
        Сохранение токенизатора в файл.

        Args:
            filepath: Путь для сохранения
        """
        data = self._prepare_save_data()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Токенизатор сохранен в {filepath}")

    def _prepare_save_data(self) -> Dict:
        """
        Подготовка данных для сохранения.

        Returns:
            Dict: Данные для сохранения
        """
        return {
            'vocab': self.vocab,
            'merges': self.merges,
            'num_merges': self.num_merges,
            'unk_token': self.unk_token,
            'unk_id': self.unk_id,
            'pad_token': self.pad_token,
            'pad_id': self.pad_id
        }

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

        tokenizer = cls._create_from_loaded_data(data)

        print(f"Токенизатор загружен из {filepath}")
        print(f"Размер словаря: {len(tokenizer.vocab)} токенов")

        return tokenizer

    @classmethod
    def _create_from_loaded_data(cls, data: Dict) -> 'BPETokenizer':
        """
        Создание токенизатора из загруженных данных.

        Args:
            data: Загруженные данные

        Returns:
            BPETokenizer: Созданный токенизатор
        """
        tokenizer = cls(num_merges=data['num_merges'])

        # Конвертируем ключи vocab в int
        tokenizer.vocab = {int(k): v for k, v in data['vocab'].items()}
        tokenizer.merges = data['merges']
        tokenizer.unk_token = data['unk_token']
        tokenizer.unk_id = data['unk_id']
        tokenizer.pad_token = data['pad_token']
        tokenizer.pad_id = data['pad_id']

        tokenizer._update_token_to_id()

        return tokenizer

    def _split_text_into_words(self, text: str) -> List[str]:
        """
        Разбиение текста на слова с добавлением специального символа.

        Args:
            text: Входной текст

        Returns:
            Список слов с специальным символом
        """
        words = []
        tokens = text.split()

        for i, token in enumerate(tokens):
            if i == 0:
                words.append(token)
            else:
                words.append('Ġ' + token)

        return words

    def _update_token_to_id(self) -> None:
        """Обновление обратного отображения token->id."""
        self.token_to_id = {v: k for k, v in self.vocab.items()}

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

    def get_merge_rules(self) -> List[Tuple[Tuple[str, str], str]]:
        """Получение правил слияния."""
        return self.merges.copy()

    def get_vocab_items(self) -> List[Tuple[int, str]]:
        """Получение элементов словаря."""
        return sorted(self.vocab.items())
