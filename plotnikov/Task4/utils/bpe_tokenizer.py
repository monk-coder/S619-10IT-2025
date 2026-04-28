import re
from collections import defaultdict

class BPETokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = {}
        self.token_to_id = {}
        self.id_to_token = {}

    def _get_stats(self, tokens):
        pairs = defaultdict(int)
        for token in tokens:
            symbols = token if isinstance(token, list) else list(token)
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i+1])] += 1
        return pairs

    def _merge_pair(self, pair, tokens):
        new_tokens = []
        i = 0
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i:i+2] == list(pair):
                new_tokens.append(''.join(pair))
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens

    def train(self, text):
        words = re.findall(r"[a-zA-Z]+|[^a-zA-Z\s]", text.lower())
        vocab = defaultdict(int)
        for word in words:
            vocab[tuple(word)] += 1
        self.vocab = {chr(i): i for i in range(256)}
        
        while len(self.vocab) < self.vocab_size:
            pairs = self._get_stats(vocab.keys())
            if not pairs: break
            best_pair = max(pairs, key=pairs.get)
            self.merges[best_pair] = len(self.vocab)
            new_token = ''.join(best_pair)
            self.vocab[new_token] = len(self.vocab)
            
            new_vocab = {}
            for tokens, freq in vocab.items():
                new_tokens = self._merge_pair(best_pair, list(tokens))
                new_vocab[tuple(new_tokens)] = freq
            vocab = new_vocab
        
        for token, idx in self.vocab.items():
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token

    def encode(self, text):
        text = text.lower()
        tokens = re.findall(r"[a-zA-Z]+|[^a-zA-Z\s]", text)
        ids = []
        for token in tokens:
            if token in self.token_to_id:
                ids.append(self.token_to_id[token])
            else:
                for char in token:
                    if char in self.token_to_id:
                        ids.append(self.token_to_id[char])
        return ids

    def decode(self, ids):
        return ''.join(self.id_to_token.get(i, '') for i in ids)

    @property
    def vocab_len(self):
        return len(self.token_to_id)