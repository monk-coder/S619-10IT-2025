import json
from collections import defaultdict
from tqdm import tqdm


class BPETokenizer:
    def __init__(self):
        self.token2id = {}
        self.id2token = {}
        self.merges = []
        self.merge_rank = {}
        self.vocab = self.token2id

    def _get_word_freqs(self, corpus):
        freqs = defaultdict(int)
        for line in corpus:
            words = line.split(" ")
            for i, w in enumerate(words):
                if i == 0:
                    freqs[w] += 1
                else:
                    freqs[" " + w] += 1
        return freqs

    def _get_pair_freqs(self, word_freqs, word_tokens):
        pair_freqs = defaultdict(int)
        for word, freq in word_freqs.items():
            tokens = word_tokens[word]
            if len(tokens) < 2:
                continue
            for i in range(len(tokens) - 1):
                pair_freqs[(tokens[i], tokens[i + 1])] += freq
        return pair_freqs

    def _merge_word(self, tokens, pair):
        new_tokens = []
        i = 0
        replacement = pair[0] + pair[1]
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(replacement)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return tuple(new_tokens)

    def train(self, corpus, num_merges=1000):
        word_freqs = self._get_word_freqs(corpus)

        unique_chars = set()
        for word in word_freqs:
            for ch in word:
                unique_chars.add(ch)

        self.token2id = {}
        for i, ch in enumerate(sorted(unique_chars)):
            self.token2id[ch] = i
        self.id2token = {i: t for t, i in self.token2id.items()}
        self.merges = []
        self.merge_rank = {}
        self.vocab = self.token2id

        next_id = len(self.token2id)

        word_tokens = {word: tuple(word) for word in word_freqs}
        pair_freqs = self._get_pair_freqs(word_freqs, word_tokens)

        for step in tqdm(range(num_merges)):
            if not pair_freqs:
                break

            best_pair = max(pair_freqs, key=pair_freqs.get)
            if pair_freqs[best_pair] < 2:
                break

            new_token = best_pair[0] + best_pair[1]
            self.merges.append(best_pair)
            self.merge_rank[best_pair] = step
            self.token2id[new_token] = next_id
            self.id2token[next_id] = new_token
            next_id += 1

            words_to_update = []
            for word, tokens in word_tokens.items():
                for i in range(len(tokens) - 1):
                    if tokens[i] == best_pair[0] and tokens[i + 1] == best_pair[1]:
                        words_to_update.append(word)
                        break

            for word in words_to_update:
                old_tokens = word_tokens[word]
                freq = word_freqs[word]

                for i in range(len(old_tokens) - 1):
                    p = (old_tokens[i], old_tokens[i + 1])
                    pair_freqs[p] -= freq
                    if pair_freqs[p] <= 0:
                        del pair_freqs[p]

                new_tokens = self._merge_word(old_tokens, best_pair)
                word_tokens[word] = new_tokens

                for i in range(len(new_tokens) - 1):
                    p = (new_tokens[i], new_tokens[i + 1])
                    pair_freqs[p] += freq

        self.vocab = self.token2id

    def _bpe_word(self, tokens):
        if len(tokens) <= 1:
            return tokens

        while True:
            best_rank = None
            best_idx = -1

            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                rank = self.merge_rank.get(pair, None)
                if rank is not None:
                    if best_rank is None or rank < best_rank:
                        best_rank = rank
                        best_idx = i

            if best_idx == -1:
                break

            pair = (tokens[best_idx], tokens[best_idx + 1])
            new_token = pair[0] + pair[1]
            tokens = tokens[:best_idx] + [new_token] + tokens[best_idx + 2:]

        return tokens

    def encode(self, text):
        if not text:
            return []

        words = text.split(" ")
        word_list = []
        for i, w in enumerate(words):
            if i == 0:
                word_list.append(w)
            else:
                word_list.append(" " + w)

        result_ids = []
        for word in word_list:
            if not word:
                continue
            tokens = self._bpe_word(list(word))
            for t in tokens:
                if t in self.token2id:
                    result_ids.append(self.token2id[t])
                else:
                    for ch in t:
                        if ch in self.token2id:
                            result_ids.append(self.token2id[ch])

        return result_ids

    def decode(self, ids):
        return "".join(self.id2token[i] for i in ids if i in self.id2token)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "vocab": self.token2id,
                    "merges": [list(m) for m in self.merges],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        t = cls()
        t.token2id = data["vocab"]
        t.id2token = {int(v): k for k, v in t.token2id.items()}
        t.merges = [tuple(m) for m in data["merges"]]
        t.merge_rank = {tuple(m): i for i, m in enumerate(t.merges)}
        t.vocab = t.token2id

        return t