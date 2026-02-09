import json
from collections import defaultdict, Counter


class BPETokenizer:
    
    def __init__(self):
        self.vocab = {}     
        self.merges = []     
        self._inv_vocab = {} 
        self.val_lines = []  

    def _get_stats(self, tokens):
        pairs = defaultdict(int)
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            pairs[pair] += 1
        return pairs

    def _merge_pair(self, tokens, pair, new_token):
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens

    def train(self, file_path, num_merges=1000, val_split=0.1, show_progress=True):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip('\n') for line in f if line.strip()]
        
        if not lines:
            raise ValueError("Файл пустой!")

        all_chars = set()
        for line in lines:
            all_chars.update(line)
        
        split_idx = int(len(lines) * (1 - val_split))
        train_lines = lines[:split_idx]
        self.val_lines = lines[split_idx:]
        
        self.vocab = {ch: i for i, ch in enumerate(sorted(all_chars))}
        next_id = len(self.vocab)
        
        word_freqs = Counter()
        for line in train_lines:
            word_freqs[tuple(line)] += 1

        from tqdm import tqdm
        merge_iter = range(num_merges)
        if show_progress:
            merge_iter = tqdm(merge_iter, desc="BPE обучение", unit="слияние")
        
        for _ in merge_iter:
            stats = defaultdict(int)
            for word, freq in word_freqs.items():
                pairs = self._get_stats(list(word))
                for pair, count in pairs.items():
                    stats[pair] += count
            
            if not stats:
                break  
            
            best_pair = max(stats, key=stats.get)
            new_token = ''.join(best_pair)
            
            self.merges.append(best_pair)
            
            if new_token not in self.vocab:
                self.vocab[new_token] = next_id
                next_id += 1
            
            new_word_freqs = Counter()
            for word, freq in word_freqs.items():
                new_word = tuple(self._merge_pair(list(word), best_pair, new_token))
                new_word_freqs[new_word] += freq
            word_freqs = new_word_freqs
        
        self._inv_vocab = {v: k for k, v in self.vocab.items()}
        
        if show_progress:
            print(f"\n✅ Обучение завершено: {len(self.vocab)} токенов, {len(self.merges)} слияний")

    def encode(self, text):
        if not text:
            return []
        
        tokens = list(text)
        
        for pair in self.merges:
            new_token = ''.join(pair)
            tokens = self._merge_pair(tokens, pair, new_token)
        
        ids = []
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                for ch in token:
                    if ch in self.vocab:
                        ids.append(self.vocab[ch])
                    else:
                        raise ValueError(f"Символ '{ch}' не найден в словаре!")
        return ids

    def decode(self, ids):
        return ''.join(self._inv_vocab.get(i, '') for i in ids)

    def save(self, path):
        data = {
            "vocab": self.vocab,
            "merges": self.merges,
            "val_lines": self.val_lines
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        obj = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj.vocab = data["vocab"]
        obj.merges = [tuple(pair) for pair in data["merges"]]
        obj.val_lines = data.get("val_lines", [])
        obj._inv_vocab = {v: k for k, v in obj.vocab.items()}
        return obj
