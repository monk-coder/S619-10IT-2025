import re
from collections import defaultdict
import pickle

class SimpleBPETokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.vocab = []
        self.merges = {}
        self.token_to_id = {}
        self.id_to_token = {}

    def train(self, text):
        words = text.split()
        word_freqs = defaultdict(int)
        for word in words:
            word_freqs[word] += 1
        
        vocab = set()
        for word in word_freqs:
            for char in word:
                vocab.add(char)
        
        self.vocab = list(vocab)
        self.vocab.append('<unk>')
        
        current_vocab = {w: list(w) for w in word_freqs}
        
        for _ in range(self.vocab_size - len(self.vocab)):
            pairs = defaultdict(int)
            for word, freq in word_freqs.items():
                symbols = current_vocab[word]
                for i in range(len(symbols)-1):
                    pairs[(symbols[i], symbols[i+1])] += freq
            
            if not pairs:
                break
                
            best_pair = max(pairs, key=pairs.get)
            self.merges[best_pair] = len(self.vocab)
            self.vocab.append(best_pair[0] + best_pair[1])
            
            for word in current_vocab:
                symbols = current_vocab[word]
                new_symbols = []
                i = 0
                while i < len(symbols):
                    if i < len(symbols)-1 and (symbols[i], symbols[i+1]) == best_pair:
                        new_symbols.append(best_pair[0] + best_pair[1])
                        i += 2
                    else:
                        new_symbols.append(symbols[i])
                        i += 1
                current_vocab[word] = new_symbols

        self._build_maps()

    def _build_maps(self):
        self.token_to_id = {token: i for i, token in enumerate(self.vocab)}
        self.id_to_token = {i: token for i, token in enumerate(self.vocab)}

    def encode(self, text):
        ids = []
        for char in text:
            if char in self.token_to_id:
                ids.append(self.token_to_id[char])
            else:
                ids.append(self.token_to_id.get('<unk>', 0))
        return ids

    def decode(self, ids):
        return "".join([self.id_to_token.get(i, '') for i in ids])

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({'vocab': self.vocab, 'merges': self.merges}, f)
            
    def load(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.vocab = data['vocab']
            self.merges = data['merges']
            self._build_maps()
