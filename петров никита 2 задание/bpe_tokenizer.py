import re
import json
import os
import numpy as np
from collections import defaultdict
from tqdm import tqdm


class BPETokenizer:
    def __init__(self):
        self.vocab = {}  # token -> id
        self.ids_to_tokens = {}  # id -> token
        self.merges = []  # list of tuples (token_a, token_b)
        self.end_symbol = "</w>"

    def _get_stats(self, corpus_words):
        """
        Подсчет частот пар соседних токенов.
        corpus_words: dict {word_tuple: frequency}
        Возвращает dict {(token_i, token_j): count}
        """
        pairs = defaultdict(int)
        for word, freq in corpus_words.items():
            symbols = word
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs

    def _merge_vocab(self, pair, v_in):
        """
        Создает новый словарь, заменяя пару токенов на объединенный токен.
        """
        v_out = {}
        bigram = re.escape(' '.join(pair))
        p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
        for word in v_in:
            w_out = p.sub(''.join(pair), word)
            v_out[w_out] = v_in[word]
        return v_out

    def train(self, corpus_lines, num_merges=1000):
        """
        Обучение токенизатора.
        corpus_lines: list of strings
        """
        print(f"Starting BPE training with {num_merges} merges...")

        # 1. Предобработка: разбиваем текст на слова, добавляем маркер конца слова
        # Используем простой сплит по пробелам для начала, но сохраняем пунктуацию как часть слов
        # Для лучшего качества можно использовать regex, но для базового BPE часто достаточно split
        word_freqs = defaultdict(int)
        for line in corpus_lines:
            # Нормализация пробелов
            line = line.strip()
            if not line:
                continue
            words = line.split()
            for word in words:
                # Добавляем символ конца слова
                word_with_end = tuple(list(word) + [self.end_symbol])
                word_freqs[word_with_end] += 1

        # 2. Инициализация словаря символов
        vocab = set()
        for word in word_freqs.keys():
            for symbol in word:
                vocab.add(symbol)

        vocab = sorted(list(vocab))
        self.vocab = {token: idx for idx, token in enumerate(vocab)}
        self.ids_to_tokens = {idx: token for token, idx in self.vocab.items()}

        current_vocab = word_freqs.copy()
        self.merges = []

        # 3. Итеративное слияние
        for i in tqdm(range(num_merges)):
            pairs = self._get_stats(current_vocab)
            if not pairs:
                break

            # Находим самую частую пару
            best_pair = max(pairs, key=pairs.get)

            # Добавляем новый токен в словарь
            new_token = ''.join(best_pair)
            new_id = len(self.vocab)
            self.vocab[new_token] = new_id
            self.ids_to_tokens[new_id] = new_token

            # Сохраняем правило слияния
            self.merges.append(best_pair)

            # Обновляем корпус: заменяем лучшую пару на новый токен
            current_vocab = self._merge_vocab(best_pair, current_vocab)

        print(f"Training finished. Vocab size: {len(self.vocab)}")

    def encode_word(self, word):
        """
        Кодирование одного слова в список ID.
        """
        # Разбиваем слово на символы и добавляем конец
        word = tuple(list(word) + [self.end_symbol])

        while True:
            pairs = [(word[i], word[i + 1]) for i in range(len(word) - 1)]
            if not pairs:
                break

            # Находим пару с наименьшим индексом в списке merges (приоритет слияния)
            # Или ту, которая есть в наших правилах
            min_idx = None
            best_pair = None

            for pair in pairs:
                if pair in self.merges:
                    idx = self.merges.index(pair)
                    if min_idx is None or idx < min_idx:
                        min_idx = idx
                        best_pair = pair

            if best_pair is None:
                break

            # Сливаем пару
            new_token = ''.join(best_pair)
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and (word[i], word[i + 1]) == best_pair:
                    new_word.append(new_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)

        # Преобразуем токены в ID
        ids = [self.vocab[token] for token in word if token in self.vocab]
        return ids

    def encode(self, text):
        """
        Кодирование всего текста.
        Возвращает list[int]
        """
        all_ids = []
        words = text.split()
        for word in words:
            ids = self.encode_word(word)
            all_ids.extend(ids)
        return all_ids

    def decode(self, ids):
        """
        Декодирование списка ID обратно в строку.
        """
        tokens = [self.ids_to_tokens[idx] for idx in ids]
        # Собираем строку
        out_string = ""
        for token in tokens:
            if token.endswith(self.end_symbol):
                # Удаляем маркер конца слова и добавляем пробел
                out_string += token[:-len(self.end_symbol)] + " "
            else:
                out_string += token

        # Убираем лишний пробел в конце, если он есть
        return out_string.rstrip()

    def save(self, path="bpe_model.json"):
        data = {
            "vocab": self.vocab,
            "merges": self.merges,
            "end_symbol": self.end_symbol
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Model saved to {path}")

    def load(self, path="bpe_model.json"):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.vocab = data["vocab"]
        self.merges = [tuple(m) for m in data["merges"]]
        self.end_symbol = data["end_symbol"]
        self.ids_to_tokens = {v: k for k, v in self.vocab.items()}
        print(f"Model loaded from {path}")
