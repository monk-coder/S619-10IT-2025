# tokenizer.py
import re
from collections import defaultdict
import pickle
import os

class BPETokenizer:
    def __init__(self, vocab_size=500):
        self.vocab_size = vocab_size
        self.vocab = set()
        self.merges = {}  # (token1, token2) -> merge_id
        self.token_to_id = {}
        self.id_to_token = {}
        self.unk_id = 0
        self.special_tokens = ['<|unk|>', '<|endoftext|>']

    def preprocess(self, text):
        """Базовая предобработка: разбиваем на символы"""
        return list(text.strip())

    def get_stats(self, vocab):
        """Считаем частоту биграмм"""
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i+1])] += freq
        return pairs

    def merge_vocab(self, pair, vocab):
        """Объединяем биграмму во всём словаре"""
        new_vocab = {}
        bigram = ''.join(pair)
        for word, freq in vocab.items():
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i+1] == pair[1]:
                    new_word.append(bigram)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_vocab[tuple(new_word)] = freq
        return new_vocab

    def train(self, text):
        """Обучение BPE на тексте"""
        # Инициализация: каждый символ — отдельный токен
        symbols = list(set(text))
        vocab = {tuple([c]): text.count(c) for c in symbols if c.strip()}
        
        # Добавляем специальные токены
        for special in self.special_tokens:
            vocab[tuple([special])] = 1
        
        # BPE-слияния
        for _ in range(self.vocab_size - len(symbols) - len(self.special_tokens)):
            pairs = self.get_stats(vocab)
            if not pairs:
                break
            best_pair = max(pairs, key=pairs.get)
            self.merges[best_pair] = len(self.merges)
            vocab = self.merge_vocab(best_pair, vocab)
        
        # Построение финального словаря
        self.vocab = set()
        for word in vocab.keys():
            for token in word:
                self.vocab.add(token)
        
        # Добавляем специальные токены
        for special in self.special_tokens:
            self.vocab.add(special)
        
        # Маппинг token <-> id
        for idx, token in enumerate(sorted(self.vocab)):
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token
        
        self.unk_id = self.token_to_id.get('<|unk|>', 0)
        print(f"✅ Tokenizer trained: {len(self.token_to_id)} tokens, {len(self.merges)} merges")

    def encode(self, text, max_length=None):
        """Текст → список ID (упрощённая посимвольная версия)"""
        ids = []
        for char in text:
            token = char if char in self.token_to_id else '<|unk|>'
            ids.append(self.token_to_id[token])
        if max_length:
            ids = ids[:max_length]
        return ids

    def decode(self, ids):
        """Список ID → текст"""
        return ''.join([self.id_to_token.get(i, '<|unk|>') for i in ids])

    def save(self, path):
        """Сохранение токенизатора"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"💾 Saved tokenizer to {path}")

    @classmethod
    def load(cls, path):
        """Загрузка токенизатора"""
        with open(path, 'rb') as f:
            return pickle.load(f)

    @property
    def vocab_len(self):
        return len(self.token_to_id)