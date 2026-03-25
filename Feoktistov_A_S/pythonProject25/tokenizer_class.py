# tokenizer_class.py
import pickle


class FreshTokenizer:
    """Простой рабочий токенизатор"""

    def __init__(self):
        self.vocab_size = 0
        self.char_to_idx = {}
        self.idx_to_char = {}

    def train(self, text, max_vocab=1000):
        """Обучает на тексте"""
        chars = sorted(list(set(text)))
        self.vocab_size = min(max_vocab, len(chars))
        self.char_to_idx = {ch: i for i, ch in enumerate(chars[:self.vocab_size])}
        self.idx_to_char = {i: ch for i, ch in enumerate(chars[:self.vocab_size])}
        return self

    def encode(self, text):
        """Кодирует текст в индексы"""
        return [self.char_to_idx.get(ch, 0) for ch in text]

    def decode(self, tokens):
        """Декодирует индексы в текст"""
        return ''.join([self.idx_to_char.get(t, '?') for t in tokens])