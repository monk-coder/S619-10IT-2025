import re
from collections import defaultdict, Counter

class BPETokenizer:
    def __init__(self, vocab_size=500):
        self.vocab_size = vocab_size
        self.merges = {}
        self.vocab = {}
        self.inv_vocab = {}

    def train(self, text, verbose=False):
        words = text.strip().split()
        word_counts = Counter(words)

        chars = set()
        for w in words:
            chars.update(list(w))
        vocab = {ch: i for i, ch in enumerate(sorted(chars))}

        word_splits = {w: list(w) for w in word_counts}

        def get_stats():
            pairs = defaultdict(int)
            for w, cnt in word_counts.items():
                syms = word_splits[w]
                for i in range(len(syms)-1):
                    pairs[(syms[i], syms[i+1])] += cnt
            return pairs

        num_merges = self.vocab_size - len(vocab)
        for i in range(num_merges):
            pairs = get_stats()
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            self.merges[best] = len(vocab)
            new_token = best[0] + best[1]
            vocab[new_token] = len(vocab)
            for w in word_splits:
                new_syms = []
                j = 0
                syms = word_splits[w]
                while j < len(syms):
                    if j < len(syms)-1 and (syms[j], syms[j+1]) == best:
                        new_syms.append(new_token)
                        j += 2
                    else:
                        new_syms.append(syms[j])
                        j += 1
                word_splits[w] = new_syms
            if verbose:
                print(f"merge {i+1}: {best} -> {new_token}")

        self.vocab = vocab
        self.inv_vocab = {i: tok for tok, i in vocab.items()}

    def encode(self, text):
        words = text.strip().split()
        encoded = []
        for w in words:
            syms = list(w)
            for (a, b), idx in self.merges.items():
                new_syms = []
                j = 0
                while j < len(syms):
                    if j < len(syms)-1 and syms[j] == a and syms[j+1] == b:
                        new_syms.append(a+b) 
                        j += 2
                    else:
                        new_syms.append(syms[j])
                        j += 1
                syms = new_syms
            encoded.extend([self.vocab[s] for s in syms])
        return encoded

    def decode(self, ids):
        tokens = [self.inv_vocab[i] for i in ids]
        return ''.join(tokens)  

if __name__ == '__main__':
    with open('data.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer = BPETokenizer(vocab_size=300)
    tokenizer.train(text, verbose=True)
    import pickle
    with open('../tokenizer.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)
