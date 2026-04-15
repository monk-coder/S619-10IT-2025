import numpy as np
from collections import defaultdict
import json
import re


class BPETokenizer:
    def __init__(self, vocab_size=1000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.inverse_vocab = {}
        self.merges = []

    def get_stats(self, ids):
        """Подсчет частот пар токенов"""
        pairs = defaultdict(int)
        for i in range(len(ids) - 1):
            pairs[(ids[i], ids[i + 1])] += 1
        return pairs

    def merge(self, ids, pair, new_id):
        """Замена пары токенов на новый токен"""
        new_ids = []
        i = 0
        while i < len(ids):
            if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
                new_ids.append(new_id)
                i += 2
            else:
                new_ids.append(ids[i])
                i += 1
        return new_ids

    def train(self, text):
        """Обучение BPE токенизатора"""
        # Начальный словарь - символы
        chars = sorted(list(set(text)))
        self.vocab = {i: char for i, char in enumerate(chars)}
        self.inverse_vocab = {char: i for i, char in enumerate(chars)}

        # Преобразуем текст в токены
        ids = [self.inverse_vocab[char] for char in text]

        # BPE обучение
        for new_id in range(len(chars), self.vocab_size):
            pairs = self.get_stats(ids)
            if not pairs:
                break

            # Находим самую частую пару
            best_pair = max(pairs, key=pairs.get)
            self.merges.append(best_pair)

            # Добавляем новый токен в словарь
            new_token = self.vocab[best_pair[0]] + self.vocab[best_pair[1]]
            self.vocab[new_id] = new_token
            self.inverse_vocab[new_token] = new_id

            # Применяем слияние
            ids = self.merge(ids, best_pair, new_id)

    def encode(self, text):
        """Кодирование текста в токены"""
        # Разбиваем на слова и знаки препинания
        words = re.findall(r'\w+|[^\w\s]', text)
        ids = []

        for word in words:
            # Начинаем с символов
            tokens = list(word)

            # Применяем изученные слияния
            for pair in self.merges:
                new_tokens = []
                i = 0
                while i < len(tokens):
                    if i < len(tokens) - 1 and tokens[i] == self.vocab[pair[0]] and tokens[i + 1] == self.vocab[
                        pair[1]]:
                        new_tokens.append(self.vocab[pair[0]] + self.vocab[pair[1]])
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1
                tokens = new_tokens

            # Конвертируем в ID
            for token in tokens:
                if token in self.inverse_vocab:
                    ids.append(self.inverse_vocab[token])
                else:
                    # Если токен не найден, кодируем посимвольно
                    for char in token:
                        if char in self.inverse_vocab:
                            ids.append(self.inverse_vocab[char])

        return ids

    def decode(self, ids):
        """Декодирование токенов в текст"""
        text = ""
        for id in ids:
            if id < len(self.vocab):
                text += self.vocab[id]
        return text

    def save(self, path):
        """Сохранение токенизатора"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'vocab': self.vocab,
                'merges': self.merges,
                'vocab_size': self.vocab_size
            }, f, ensure_ascii=False)

    def load(self, path):
        """Загрузка токенизатора"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.vocab = {int(k): v for k, v in data['vocab'].items()}
            self.inverse_vocab = {v: int(k) for k, v in self.vocab.items()}
            self.merges = [tuple(m) for m in data['merges']]
            self.vocab_size = data['vocab_size']