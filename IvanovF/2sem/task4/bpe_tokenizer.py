import json
from collections import defaultdict
from tqdm import tqdm


class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.id2token = {}
        self.merges = []
        self.token2id = {}

    def train(self, corpus, num_merges=1000):
        corpus_tokens = []
        for line in corpus:
            tokens = list(line)
            corpus_tokens.append(tokens)

        unique_chars = set()
        for tokens in corpus_tokens:
            unique_chars.update(tokens)

        self.vocab = {}
        for i, ch in enumerate(sorted(unique_chars)):
            self.vocab[ch] = i

        self.token2id = dict(self.vocab)
        self.id2token = {i: t for t, i in self.token2id.items()}

        next_id = len(self.token2id)

        for _ in tqdm(range(num_merges)):
            pair_freq = self._get_pair_frequencies(corpus_tokens)
            if not pair_freq:
                break

            best_pair = max(pair_freq, key=pair_freq.get)
            if pair_freq[best_pair] < 2:
                break

            corpus_tokens = self._merge_pair(best_pair, corpus_tokens)

            new_token = best_pair[0] + best_pair[1]
            self.merges.append(best_pair)

            self.token2id[new_token] = next_id
            self.id2token[next_id] = new_token
            next_id += 1

        self.vocab = self.token2id

    def _get_pair_frequencies(self, corpus_tokens):
        freqs = defaultdict(int)
        for tokens in corpus_tokens:
            for i in range(len(tokens) - 1):
                freqs[(tokens[i], tokens[i + 1])] += 1
        return freqs

    def _merge_pair(self, pair, corpus_tokens):
        new_corpus = []
        bigram = pair
        replacement = pair[0] + pair[1]

        for tokens in corpus_tokens:
            i = 0
            new_tokens = []
            while i < len(tokens):
                if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == bigram:
                    new_tokens.append(replacement)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            new_corpus.append(new_tokens)

        return new_corpus

    def encode(self, text):
        tokens = list(text)
        for pair in self.merges:
            tokens = self._apply_merge(pair, tokens)
        # Обработка неизвестных токенов
        result = []
        for t in tokens:
            if t in self.token2id:
                result.append(self.token2id[t])
            else:
                # Пропускаем неизвестные символы (или можно добавить <unk>)
                pass
        return result

    def _apply_merge(self, pair, tokens):
        i = 0
        new_tokens = []
        replacement = pair[0] + pair[1]

        while i < len(tokens):
            if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == pair:
                new_tokens.append(replacement)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1

        return new_tokens

    def decode(self, ids):
        tokens = [self.id2token[i] for i in ids]
        return "".join(tokens)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "vocab": self.token2id,
                    "merges": self.merges,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tokenizer = cls()
        tokenizer.token2id = data["vocab"]
        tokenizer.id2token = {int(v): k for k, v in tokenizer.token2id.items()}
        tokenizer.merges = [tuple(m) for m in data["merges"]]
        tokenizer.vocab = tokenizer.token2id

        return tokenizer

    def __len__(self):
        return len(self.token2id)