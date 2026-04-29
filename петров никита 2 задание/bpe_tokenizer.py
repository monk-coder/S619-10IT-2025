import json
import os
from collections import defaultdict
from tqdm import tqdm

class BPETokenizer:
    def __init__(self):
        self.vocab = {}          # token -> id
        self.ids_to_tokens = {}  # id -> token
        self.merges = []         # list of tuples (token_a, token_b)
        self.end_symbol = "</w>"

    def _get_stats(self, word_freqs):
        """Подсчет частот соседних пар токенов."""
        pairs = defaultdict(int)
        for word, freq in word_freqs.items():
            for i in range(len(word) - 1):
                pairs[(word[i], word[i+1])] += freq
        return pairs

    def _merge_pair(self, word_freqs, pair):
        """Замена пары токенов на объединенный токен во всем корпусе."""
        new_word_freqs = defaultdict(int)
        merged_token = ''.join(pair)
        for word, freq in word_freqs.items():
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i+1] == pair[1]:
                    new_word.append(merged_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_word_freqs[tuple(new_word)] += freq
        return new_word_freqs

    def train(self, corpus_lines, num_merges=1000):
        print(f"Starting BPE training with {num_merges} merges...")

        # 1. Предобработка: разбиение на слова + маркер конца слова
        word_freqs = defaultdict(int)
        for line in corpus_lines:
            for word in line.split():
                word_freqs[tuple(list(word) + [self.end_symbol])] += 1

        # 2. Инициализация словаря символов
        base_chars = set()
        for word in word_freqs.keys():
            base_chars.update(word)
        base_chars = sorted(list(base_chars))

        self.vocab = {token: idx for idx, token in enumerate(base_chars)}
        self.ids_to_tokens = {idx: token for token, idx in self.vocab.items()}
        self.merges = []

        # 3. Итеративное слияние
        current_word_freqs = word_freqs
        for _ in tqdm(range(num_merges)):
            pairs = self._get_stats(current_word_freqs)
            if not pairs:
                break

            best_pair = max(pairs, key=pairs.get)
            new_token = ''.join(best_pair)

            new_id = len(self.vocab)
           
