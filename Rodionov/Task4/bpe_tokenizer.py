import re
from collections import Counter


class BPETokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.inverse_vocab = {}
        self.merges = {}

    def train(self, texts):
        """Обучение BPE токенизатора на корпусе текстов"""
        # Начальный словарь символов
        word_freqs = Counter()
        for text in texts:
            words = text.split()
            for word in words:
                word_freqs[' '.join(list(word)) + ' </w>'] += 1

        # Начальный словарь символов
        vocab = {}
        for word in word_freqs:
            for char in word.split():
                vocab[char] = vocab.get(char, 0) + word_freqs[word]

        # BPE мержи
        num_merges = self.vocab_size - len(vocab)

        for i in range(num_merges):
            pairs = Counter()
            for word, freq in word_freqs.items():
                symbols = word.split()
                for j in range(len(symbols) - 1):
                    pairs[(symbols[j], symbols[j + 1])] += freq

            if not pairs:
                break

            most_common = max(pairs, key=pairs.get)
            self.merges[most_common] = len(vocab)

            # Обновляем словарь
            new_word_freqs = Counter()
            for word, freq in word_freqs.items():
                new_word = word.replace(' '.join(most_common), ''.join(most_common))
                new_word_freqs[new_word] = freq
            word_freqs = new_word_freqs

            # Обновляем vocab
            vocab[''.join(most_common)] = pairs[most_common]

        # Создаем финальный словарь
        self.vocab = {i: token for i, (token, _) in enumerate(sorted(vocab.items(), key=lambda x: -x[1]))}
        self.inverse_vocab = {token: i for i, token in self.vocab.items()}

        # Добавляем специальные токены
        self.vocab[self.vocab_size - 3] = '<PAD>'
        self.vocab[self.vocab_size - 2] = '<UNK>'
        self.vocab[self.vocab_size - 1] = '<EOS>'
        self.inverse_vocab['<PAD>'] = self.vocab_size - 3
        self.inverse_vocab['<UNK>'] = self.vocab_size - 2
        self.inverse_vocab['<EOS>'] = self.vocab_size - 1

    def encode(self, text):
        """Кодирование текста в токены"""
        words = text.split()
        encoded = []
        for word in words:
            tokens = list(word) + ['</w>']
            merged = False
            while not merged:
                merged = True
                for i in range(len(tokens) - 1):
                    if (tokens[i], tokens[i + 1]) in self.merges:
                        tokens[i] = tokens[i] + tokens[i + 1]
                        tokens.pop(i + 1)
                        merged = False
                        break
            for token in tokens:
                if token in self.inverse_vocab:
                    encoded.append(self.inverse_vocab[token])
                else:
                    encoded.append(self.inverse_vocab['<UNK>'])
        return encoded

    def decode(self, tokens):
        """Декодирование токенов в текст"""
        text = ''
        for token in tokens:
            if token in self.vocab:
                token_str = self.vocab[token]
                if token_str == '<EOS>':
                    break
                elif token_str == '<PAD>' or token_str == '<UNK>':
                    continue
                elif token_str.endswith('</w>'):
                    text += token_str[:-4] + ' '
                else:
                    text += token_str
        return text.strip()