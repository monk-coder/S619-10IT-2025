import json
import re
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import numpy as np
from tqdm import tqdm


class BPETokenizer:
    """BPE Tokenizer implementation from scratch."""
    
    def __init__(self, vocab_size: Optional[int] = None):
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.merges: List[Tuple[str, str]] = []
        self.vocab_size = vocab_size
        self.special_tokens = {"<unk>": 0, "<pad>": 1, "<s>": 2, "</s>": 3}
        
    def _get_stats(self, token_freqs: Dict[str, int]) -> Dict[Tuple[str, str], int]:
        pairs = defaultdict(int)
        for token, freq in token_freqs.items():
            symbols = token.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs
    
    def _merge_pair(self, pair: Tuple[str, str], token_freqs: Dict[str, int]) -> Dict[str, int]:
        new_token_freqs = {}
        bigram = " ".join(pair)
        replacement = "".join(pair)
        
        for token, freq in token_freqs.items():
            new_token_str = token.replace(bigram, replacement)
            new_token_freqs[new_token_str] = freq
        
        return new_token_freqs
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        token_freqs = defaultdict(int)
        
        if verbose:
            print("Preprocessing text...")
        
        for text in tqdm(corpus, disable=not verbose, desc="Processing"):
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    bpe_token = " ".join(list(word))
                    token_freqs[bpe_token] += 1
        
        chars = set()
        for token in token_freqs.keys():
            chars.update(token.split())
        
        sorted_chars = sorted(chars)
        self.vocab = {char: i + len(self.special_tokens) for i, char in enumerate(sorted_chars)}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        self.vocab_size = len(self.vocab)
        
        if verbose:
            print(f"Base vocabulary: {len(chars)} chars, size: {self.vocab_size}")
            if num_merges > 0:
                print(f"Performing {num_merges} merges...")
        
        for _ in tqdm(range(num_merges), disable=not verbose or num_merges == 0, desc="Merges"):
            pairs = self._get_stats(token_freqs)
            
            if not pairs:
                break
            
            best_pair = max(pairs.items(), key=lambda x: (x[1], x[0]))[0]
            
            if pairs[best_pair] < 2:
                break
            
            self.merges.append(best_pair)
            token_freqs = self._merge_pair(best_pair, token_freqs)
            
            new_token = "".join(best_pair)
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
                self.vocab_size += 1
        
        if verbose:
            print(f"Training completed. Vocab size: {self.vocab_size}, Merges: {len(self.merges)}")
    
    def _apply_merges(self, word: str) -> List[str]:
        tokens = list(word)
        
        for pair in self.merges:
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                    new_tokens.append(pair[0] + pair[1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            
            if len(new_tokens) < len(tokens):
                tokens = new_tokens
        
        return tokens
    
    def encode(self, text: str) -> List[int]:
        text = unicodedata.normalize('NFKC', text)
        words = text.split()
        
        ids = []
        for word in words:
            bpe_tokens = self._apply_merges(word)
            
            for token in bpe_tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    for char in token:
                        if char in self.vocab:
                            ids.append(self.vocab[char])
                        else:
                            ids.append(self.special_tokens["<unk>"])
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        tokens = []
        for id_ in ids:
            if id_ in self.id_to_token:
                tokens.append(self.id_to_token[id_])
            else:
                tokens.append("<unk>")
        
        return " ".join(tokens)
    
    def save(self, filepath: str):
        data = {
            'vocab': self.vocab,
            'merges': [list(pair) for pair in self.merges],
            'vocab_size': self.vocab_size,
            'special_tokens': self.special_tokens
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.vocab_size = data['vocab_size']
        self.special_tokens = data['special_tokens']
        self.id_to_token = {v: k for k, v in self.vocab.items()}


def split_train_val(corpus: List[str], val_ratio: float = 0.1) -> Tuple[List[str], List[str]]:
    shuffled = corpus.copy()
    np.random.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1 - val_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]


def calculate_metrics(tokenizer: BPETokenizer, val_corpus: List[str]) -> Dict:
    lengths = []
    
    for text in val_corpus:
        ids = tokenizer.encode(text)
        lengths.append(len(ids))
    
    if not lengths:
        return {
            'vocab_size': tokenizer.vocab_size,
            'avg_length': 0.0,
            'median_length': 0.0,
            'std_length': 0.0,
            'min_length': 0,
            'max_length': 0,
            'long_sequences_ratio': 0.0,
            'long_threshold': 0.0
        }
    
    lengths_array = np.array(lengths)
    threshold = np.percentile(lengths_array, 99)
    
    return {
        'vocab_size': tokenizer.vocab_size,
        'avg_length': float(np.mean(lengths_array)),
        'median_length': float(np.median(lengths_array)),
        'std_length': float(np.std(lengths_array)),
        'min_length': int(np.min(lengths_array)),
        'max_length': int(np.max(lengths_array)),
        'long_sequences_ratio': float(np.mean(lengths_array > threshold)),
        'long_threshold': float(threshold)
    }
