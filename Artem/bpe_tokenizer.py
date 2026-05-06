# bpe_tokenizer.py
import re
import json
from collections import defaultdict

class BPE_Tokenizer:
    def __init__(self):
        self.encoder = {}  # token -> id
        self.decoder = {}  # id -> token
        self.merges = {}   # (str, str) -> id
        self.eos_token = "<|endoftext|>"
        # Регулярка сохраняет пробелы как отдельные токены
        self.split_pattern = re.compile(r'[^\s]+|\s+')

    def train(self, text, vocab_size=5000):
        # 1. Базовый словарь: все уникальные символы + EOS
        chars = sorted(list(set(text)))
        self.encoder = {c: i for i, c in enumerate(chars)}
        self.encoder[self.eos_token] = len(self.encoder)
        self.decoder = {v: k for k, v in self.encoder.items()}

        # 2. Разбиваем текст на токены (слова/пробелы), добавляем маркер конца слова
        tokens_list = self.split_pattern.findall(text)
        corpus = []
        for t in tokens_list:
            corpus.append(list(t) + ['</w>'])

        freqs = defaultdict(int)
        for w in corpus:
            freqs[tuple(w)] += 1

        # 3. BPE итерации
        for _ in range(vocab_size - len(self.encoder)):
            pairs = defaultdict(int)
            for w, f in freqs.items():
                for i in range(len(w)-1):
                    pairs[(w[i], w[i+1])] += f

            if not pairs:
                break

            best_pair = max(pairs, key=pairs.get)
            new_token = best_pair[0] + best_pair[1]
            new_id = len(self.encoder)

            self.encoder[new_token] = new_id
            self.decoder[new_id] = new_token
            self.merges[best_pair] = new_id

            # Обновляем корпус
            new_freqs = defaultdict(int)
            for w, f in freqs.items():
                new_w = []
                i = 0
                while i < len(w):
                    if i < len(w)-1 and (w[i], w[i+1]) == best_pair:
                        new_w.append(new_token)
                        i += 2
                    else:
                        new_w.append(w[i])
                        i += 1
                new_freqs[tuple(new_w)] += f
            freqs = new_freqs

    def encode(self, text: str) -> list[int]:
        tokens = self.split_pattern.findall(text)
        ids = []
        for t in tokens:
            seq = list(t) + ['</w>']
            while True:
                # Находим лучшую пару для слияния
                best_pair, best_rank = None, float('inf')
                for i in range(len(seq)-1):
                    pair = (seq[i], seq[i+1])
                    if pair in self.merges and self.merges[pair] < best_rank:
                        best_pair = pair
                        best_rank = self.merges[pair]
                if best_pair is None:
                    break
                # Применяем слияние
                new_seq = []
                i = 0
                while i < len(seq):
                    if i < len(seq)-1 and (seq[i], seq[i+1]) == best_pair:
                        new_seq.append(best_pair[0] + best_pair[1])
                        i += 2
                    else:
                        new_seq.append(seq[i])
                        i += 1
                seq = new_seq
            for s in seq:
                ids.append(self.encoder.get(s, 0))
        return ids

    def decode(self, ids: list[int]) -> str:
        text = "".join(self.decoder.get(i, self.eos_token) for i in ids)
        text = text.replace("</w>", "")
        return text

    @property
    def vocab_size(self) -> int:
        return len(self.encoder)

    def save(self, path: str):
        # Сериализуем merges в JSON-friendly формате
        merges_list = [f"{k[0]}|{k[1]}" for k in self.merges]
        data = {"encoder": self.encoder, "merges_list": merges_list, "eos": self.eos_token}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tok = cls()
        tok.encoder = data["encoder"]
        tok.decoder = {v: k for k, v in tok.encoder.items()}
        tok.merges = {tuple(k.split("|")): v for v, k in enumerate(data["merges_list"])}
        tok.eos_token = data["eos"]
        return tok