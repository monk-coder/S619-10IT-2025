import json
import os
from typing import List, Dict, Tuple
from collections import Counter
import numpy as np


class BPETokenizer:
    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.inverse_vocab: Dict[int, str] = {}
        self.merges: List[Tuple[str, str]] = []
        self.vocab_size = 0

    def train(self, corpus: List[str], num_merges: int) -> None:
        print(f"🧠 Обучение BPE: {num_merges:,} слияний")

        # Базовый словарь из символов
        chars = set()
        for line in corpus:
            chars.update(line)

        sorted_chars = sorted(chars)
        for i, char in enumerate(sorted_chars):
            self.vocab[char] = i
            self.inverse_vocab[i] = char
        self.vocab_size = len(self.vocab)

        words = [list(line) for line in corpus]

        for step in range(num_merges):
            pairs = self._get_pairs(words)
            if not pairs:
                break

            pair = pairs.most_common(1)[0][0]
            new_token = pair[0] + pair[1]

            self.vocab[new_token] = self.vocab_size
            self.inverse_vocab[self.vocab_size] = new_token
            self.vocab_size += 1

            self.merges.append(pair)
            words = self._merge_all(words, pair)

            if step % 1000 == 0 or step < 10:
                print(f"  {step:4d}: '{pair[0]}'+ '{pair[1]}' → '{new_token}'")

        print(f"✅ Словарь: {self.vocab_size:,}")

    def _get_pairs(self, words: List[List[str]]) -> Counter:
        pairs = Counter()
        for word in words:
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += 1
        return pairs

    def _merge_all(self, words: List[List[str]], pair: Tuple[str, str]) -> List[List[str]]:
        new_words = []
        for word in words:
            new_word = []
            i = 0
            while i < len(word):
                if i + 1 < len(word) and word[i] == pair[0] and word[i + 1] == pair[1]:
                    new_word.append(pair[0] + pair[1])
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_words.append(new_word)
        return new_words

    def encode(self, text: str) -> List[int]:
        """✅ ИСПРАВЛЕНО: поддержка неизвестных токенов"""
        if not text:
            return []

        word = list(text)
        for pair in self.merges:
            word = self._merge_one(word, pair)

        # ✅ Автоматически добавляем неизвестные токены
        result_ids = []
        for t in word:
            if t not in self.vocab:
                self.vocab[t] = self.vocab_size
                self.inverse_vocab[self.vocab_size] = t
                self.vocab_size += 1
            result_ids.append(self.vocab[t])

        return result_ids

    def _merge_one(self, word: List[str], pair: Tuple[str, str]) -> List[str]:
        new_word = []
        i = 0
        while i < len(word):
            if i + 1 < len(word) and word[i] == pair[0] and word[i + 1] == pair[1]:
                new_word.append(pair[0] + pair[1])
                i += 2
            else:
                new_word.append(word[i])
                i += 1
        return new_word

    def decode(self, ids: List[int]) -> str:
        return ''.join(self.inverse_vocab[i] for i in ids)

    def save(self, path: str):
        if '.' in path:
            dir_path = os.path.dirname(path)
            if dir_path and dir_path != '':
                os.makedirs(dir_path, exist_ok=True)

        data = {
            'merges': [[m[0], m[1]] for m in self.merges],
            'vocab': self.vocab,
            'vocab_size': self.vocab_size
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {path}")

    @classmethod
    def load(cls, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tokenizer = cls()
        tokenizer.merges = [tuple(m) for m in data['merges']]
        tokenizer.vocab = data['vocab']
        tokenizer.inverse_vocab = {v: k for k, v in data['vocab'].items()}
        tokenizer.vocab_size = data['vocab_size']
        print(f"📂 Загружено: {path} (словарь: {tokenizer.vocab_size:,})")
        return tokenizer


def split_corpus(corpus_path: str, train_ratio: float = 0.9) -> tuple[List[str], List[str]]:
    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"❌ Файл не найден: {corpus_path}")

    with open(corpus_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.read().splitlines() if line.strip()]

    np.random.seed(42)
    n = len(lines)
    split = int(n * train_ratio)

    return lines[:split], lines[split:]
