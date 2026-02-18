import json
import os
from collections import Counter, defaultdict
from typing import List, Dict, Tuple


class BPETokenizer:
    
    def __init__(self) -> None:
        self.vocab: Dict[str, int] = {}
        self.merges: List[Tuple[str, str]] = []
        self._inv_vocab: Dict[int, str] = {}
        self.val_lines: List[str] = []
    
    def _get_pair_stats(self, tokens: List[str]) -> Dict[Tuple[str, str], int]:
        stats = defaultdict(int)
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            stats[pair] += 1
        return stats
    
    def _merge_tokens(self, tokens: List[str], pair: Tuple[str, str], replacement: str) -> List[str]:
        result = []
        i = 0
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                result.append(replacement)
                i += 2
            else:
                result.append(tokens[i])
                i += 1
        return result
    
    def find_data_file(self) -> str:
        current_dir = os.getcwd()
        
        for root, dirs, files in os.walk(current_dir):
            if 'S619-10IT-2025' in root:
                target_dir = os.path.join(root, '0')
                if os.path.exists(target_dir):
                    data_path = os.path.join(target_dir, 'data.txt')
                    if os.path.exists(data_path):
                        return data_path
        
        parent_dir = os.path.dirname(current_dir)
        for root, dirs, files in os.walk(parent_dir):
            if 'S619-10IT-2025' in root:
                target_dir = os.path.join(root, '0')
                if os.path.exists(target_dir):
                    data_path = os.path.join(target_dir, 'data.txt')
                    if os.path.exists(data_path):
                        return data_path
        
        search_dirs = [
            os.path.join(current_dir, 'S619-10IT-2025', '0'),
            os.path.join(parent_dir, 'S619-10IT-2025', '0'),
            os.path.join(os.path.dirname(parent_dir), 'S619-10IT-2025', '0'),
            os.path.join(current_dir, '..', 'S619-10IT-2025', '0'),
            os.path.join(current_dir, '0'),
            os.path.join(current_dir, '..', '0')
        ]
        
        for dir_path in search_dirs:
            data_path = os.path.join(dir_path, 'data.txt')
            if os.path.exists(data_path):
                return os.path.abspath(data_path)
        
        return 'data.txt'
    
    def train(
        self,
        file_path: str = None,
        num_merges: int = 1000,
        val_split: float = 0.1,
        show_progress: bool = True
    ) -> None:
        if file_path is None:
            file_path = self.find_data_file()
        
        if not 0.0 <= val_split <= 1.0:
            raise ValueError(f"val_split must be between 0 and 1, got {val_split}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not lines:
            raise ValueError(f"File {file_path} is empty or contains only whitespace")
        
        all_chars = set()
        for line in lines:
            all_chars.update(line)
        
        split_idx = int(len(lines) * (1 - val_split))
        train_lines = lines[:split_idx]
        self.val_lines = lines[split_idx:]
        
        self.vocab = {ch: idx for idx, ch in enumerate(sorted(all_chars))}
        next_id = len(self.vocab)
        
        word_freqs = Counter()
        for line in train_lines:
            word_freqs[tuple(line)] += 1
        
        if show_progress:
            try:
                from tqdm import tqdm
                merge_range = tqdm(
                    range(num_merges),
                    desc="Training BPE",
                    unit="merge",
                    ncols=80
                )
            except ImportError:
                merge_range = range(num_merges)
        else:
            merge_range = range(num_merges)
        
        for _ in merge_range:
            pair_stats = defaultdict(int)
            for word, freq in word_freqs.items():
                for pair, count in self._get_pair_stats(list(word)).items():
                    pair_stats[pair] += count
            
            if not pair_stats:
                break
            
            best_pair = max(pair_stats, key=pair_stats.get)
            new_token = ''.join(best_pair)
            
            self.merges.append(best_pair)
            
            if new_token not in self.vocab:
                self.vocab[new_token] = next_id
                next_id += 1
            
            new_word_freqs = Counter()
            for word, freq in word_freqs.items():
                merged_word = tuple(self._merge_tokens(list(word), best_pair, new_token))
                new_word_freqs[merged_word] += freq
            word_freqs = new_word_freqs
        
        self._inv_vocab = {idx: token for token, idx in self.vocab.items()}
    
    def encode(self, text: str) -> List[int]:
        if not text:
            return []
        
        tokens = list(text)
        
        for pair in self.merges:
            new_token = ''.join(pair)
            tokens = self._merge_tokens(tokens, pair, new_token)
        
        ids = []
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                for char in token:
                    if char in self.vocab:
                        ids.append(self.vocab[char])
                    else:
                        raise ValueError(
                            f"Character '{char}' not in vocabulary. "
                            f"Ensure all characters are present in training corpus."
                        )
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        return ''.join(self._inv_vocab.get(idx, '') for idx in ids)
    
    def save(self, path: str) -> None:
        data = {
            'vocab': self.vocab,
            'merges': self.merges,
            'val_lines': self.val_lines
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'BPETokenizer':
        obj = cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        obj.vocab = data['vocab']
        obj.merges = [tuple(pair) for pair in data['merges']]
        obj.val_lines = data.get('val_lines', [])
        obj._inv_vocab = {idx: token for token, idx in obj.vocab.items()}
        
        return obj
    
    def __len__(self) -> int:
        return len(self.vocab)
    
    def __repr__(self) -> str:
        return f"BPETokenizer(vocab_size={len(self.vocab)}, merges={len(self.merges)})"
