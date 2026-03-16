import json
import re


class BPETokenizer:
    def __init__(self, special_tokens=None):
        self.merges = {}  # (id_a, id_b) -> new_id
        self.vocab = {}  # id -> bytes
        self.special_tokens = special_tokens or {}  # {"<|endoftext|>": 10000}
        self.inverse_special = {v: k for k, v in self.special_tokens.items()}

    def train(self, text, vocab_size, verbose=True):
        # 1. Начальные токены — это байты 0-255
        tokens = list(text.encode("utf-8"))
        self.vocab = {i: bytes([i]) for i in range(256)}

        num_merges = vocab_size - 256 - len(self.special_tokens)

        for i in range(num_merges):
            # Считаем пары
            stats = {}
            for pair in zip(tokens, tokens[1:]):
                stats[pair] = stats.get(pair, 0) + 1

            if not stats: break

            best_pair = max(stats, key=stats.get)
            new_id = 256 + i

            # Обновляем список токенов (слияние)
            new_tokens = []
            skip = False
            for j in range(len(tokens)):
                if skip:
                    skip = False
                    continue
                if j < len(tokens) - 1 and (tokens[j], tokens[j + 1]) == best_pair:
                    new_tokens.append(new_id)
                    skip = True
                else:
                    new_tokens.append(tokens[j])
            tokens = new_tokens

            self.merges[best_pair] = new_id
            self.vocab[new_id] = self.vocab[best_pair[0]] + self.vocab[best_pair[1]]

            if verbose and (i + 1) % 500 == 0:
                print(f"Merge {i + 1}/{num_merges} complete")

        # Добавляем спец. токены в словарь в самом конце
        for token, idx in self.special_tokens.items():
            self.vocab[idx] = token.encode("utf-8")

    def encode(self, text, allowed_special=True):
        # Если в тексте есть спец. токены, обрабатываем их отдельно через regex
        if not self.special_tokens:
            tokens = list(text.encode("utf-8"))
        else:
            # Упрощенный поиск спецтокенов
            special_pattern = "(" + "|".join(map(re.escape, self.special_tokens.keys())) + ")"
            parts = re.split(special_pattern, text)
            tokens = []
            for part in parts:
                if part in self.special_tokens:
                    tokens.append(self.special_tokens[part])
                else:
                    # Обычный текст кодируем через накопленные merges
                    sub_tokens = list(part.encode("utf-8"))
                    while len(sub_tokens) >= 2:
                        # Ищем пару с минимальным индексом в merges (самую раннюю)
                        stats = [(self.merges.get((sub_tokens[i], sub_tokens[i + 1]), float('inf')), i)
                                 for i in range(len(sub_tokens) - 1)]
                        best_merge, idx = min(stats)
                        if best_merge == float('inf'): break

                        # Сливаем
                        sub_tokens = sub_tokens[:idx] + [best_merge] + sub_tokens[idx + 2:]
                    tokens.extend(sub_tokens)
        return tokens

    def decode(self, ids):
        byte_parts = []
        for idx in ids:
            if idx in self.vocab:
                byte_parts.append(self.vocab[idx])
            else:
                # На случай поврежденных ID
                byte_parts.append(b"")
        return b"".join(byte_parts).decode("utf-8", errors="replace")

    def save(self, path="bpe_model.json"):
        # Преобразуем кортежи-ключи в строки для JSON: "id1,id2"
        serializable_merges = {f"{k[0]},{k[1]}": v for k, v in self.merges.items()}
        # Байты в строку через latin-1 (сохраняет каждый байт как символ)
        serializable_vocab = {k: v.decode('latin-1') for k, v in self.vocab.items()}

        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "merges": serializable_merges,
                "vocab": serializable_vocab,
                "special": self.special_tokens
            }, f)

    def load(self, path="bpe_model.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.merges = {tuple(map(int, k.split(","))): v for k, v in data["merges"].items()}
        self.vocab = {int(k): v.encode('latin-1') for k, v in data["vocab"].items()}
        self.special_tokens = data["special"]
        self.inverse_special = {v: k for k, v in self.special_tokens.items()}
