import os
import json
from collections import defaultdict

class BPETokenizer:
    def __init__(self, vocab_size=1000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = []
        self.token_to_id = {}
        self.id_to_token = {}
        self.special_tokens = ["<pad>", "<unk>", "<bos>", "<eos>"]
        
    def train(self, text):
        # Инициализация символов
        vocab = set(text)
        for tok in self.special_tokens:
            vocab.add(tok)
        
        # Токенизация по символам
        words = text.split()
        word_freqs = defaultdict(int)
        for word in words:
            word_freqs[word] += 1
            
        # Представление слов как списков символов
        split_words = {word: list(word) for word in word_freqs.keys()}
        
        self.merges = []
        
        # Обучение слияний
        while len(self.token_to_id) < self.vocab_size - len(self.special_tokens):
            pairs = defaultdict(int)
            for word, freq in word_freqs.items():
                symbols = split_words[word]
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i+1])] += freq
            
            if not pairs:
                break
                
            best_pair = max(pairs, key=pairs.get)
            self.merges.append(best_pair)
            
            # Выполнение слияния
            new_vocab = set()
            for word in split_words:
                symbols = split_words[word]
                new_symbols = []
                i = 0
                while i < len(symbols):
                    if i < len(symbols) - 1 and (symbols[i], symbols[i+1]) == best_pair:
                        new_symbols.append("".join(best_pair))
                        i += 2
                    else:
                        new_symbols.append(symbols[i])
                        i += 1
                split_words[word] = new_symbols
                new_vocab.update(new_symbols)
            
            vocab.update(new_vocab)
            if len(vocab) >= self.vocab_size:
                break
        
        # Построение словаря
        all_tokens = sorted(list(vocab))
        # Приоритет спец токенам
        for tok in self.special_tokens:
            if tok in all_tokens:
                all_tokens.remove(tok)
        all_tokens = self.special_tokens + all_tokens[:self.vocab_size]
        
        self.token_to_id = {t: i for i, t in enumerate(all_tokens)}
        self.id_to_token = {i: t for t, i in self.token_to_id.items()}
        self.vocab_size = len(self.token_to_id)

    def encode(self, text):
        tokens = list(text)
        # Применяем слияния
        for merge in self.merges:
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] + tokens[i+1] == "".join(merge):
                    new_tokens.append("".join(merge))
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        
        ids = []
        for t in tokens:
            if t in self.token_to_id:
                ids.append(self.token_to_id[t])
            else:
                ids.append(self.token_to_id.get("<unk>", 1))
        return ids

    def decode(self, ids):
        tokens = [self.id_to_token.get(i, "<unk>") for i in ids]
        return "".join(tokens)

    def save(self, path):
        data = {
            "vocab_size": self.vocab_size,
            "merges": self.merges,
            "token_to_id": self.token_to_id,
            "id_to_token": self.id_to_token
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.vocab_size = data["vocab_size"]
        self.merges = [tuple(m) for m in data["merges"]]
        self.token_to_id = data["token_to_id"]
        self.id_to_token = {int(k): v for k, v in data["id_to_token"].items()}

def get_or_create_data(path="data.txt"):
    if not os.path.exists(path):
        print(f"[Warning] {path} not found. Creating dummy dataset...")
        # Простой текст для демонстрации обучения
        text = "The quick brown fox jumps over the lazy dog. " * 500
        text += "Artificial intelligence is transforming the world. " * 500
        text += "Deep learning models require large amounts of data. " * 500
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()