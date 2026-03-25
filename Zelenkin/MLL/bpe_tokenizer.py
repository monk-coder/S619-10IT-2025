import numpy as np
from collections import defaultdict, Counter


class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.merges = {}
        self.byte_encoder = {}

    def _get_stats(self, vocab):
        """Подсчет частот пар"""
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[symbols[i], symbols[i + 1]] += freq
        return pairs

    def _merge_vocab(self, pair, vocab):
        """Слияние пары в словаре"""
        v_out = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)
        for word in vocab:
            w_out = word.replace(bigram, replacement)
            v_out[w_out] = vocab[word]
        return v_out

    def train(self, text, num_merges=500):
        """Обучение BPE"""
        # Инициализация словаря символами
        words = text.split()
        vocab = defaultdict(int)
        for word in words:
            vocab[' '.join(list(word)) + ' </w>'] += 1

        self.vocab = vocab.copy()

        for i in range(num_merges):
            pairs = self._get_stats(vocab)
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            vocab = self._merge_vocab(best, vocab)
            self.merges[best] = i

        # Создание словаря токенов
        tokens = set()
        for word in vocab:
            tokens.update(word.split())

        self.vocab = {token: idx for idx, token in enumerate(sorted(tokens))}

    def encode(self, text):
        """Токенизация текста"""
        words = text.split()
        tokens = []
        for word in words:
            word_tokens = list(word) + ['</w>']
            for token in word_tokens:
                if token in self.vocab:
                    tokens.append(self.vocab[token])
                else:
                    tokens.append(self.vocab.get('<unk>', 0))
        return np.array(tokens, dtype=np.int32)

    def decode(self, tokens):
        """Декодирование токенов в текст"""
        idx_to_token = {v: k for k, v in self.vocab.items()}
        text = ''
        for token in tokens:
            text += idx_to_token.get(token, '<unk>')
        return text.replace('</w>', ' ')