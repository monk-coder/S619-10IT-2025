import json
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


class BPETokenizer:
    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.merges: List[Tuple[str, str]] = []
        self.special_tokens = {"<unk>": 0, "<pad>": 1, "<s>": 2, "</s>": 3}
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = False):
        # Count frequencies
        token_freqs = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    token_freqs[" ".join(list(word))] += 1
        
        # Initialize vocabulary with characters
        chars = set()
        for token in token_freqs.keys():
            chars.update(token.split())
        
        # Build vocabulary
        self.vocab = {char: i + len(self.special_tokens) for i, char in enumerate(sorted(chars))}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        # Perform BPE merges
        for _ in range(num_merges):
            # Get pair frequencies
            pairs = defaultdict(int)
            for token, freq in token_freqs.items():
                symbols = token.split()
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i + 1])] += freq
            
            if not pairs:
                break
            
            # Find most frequent pair
            best_pair = max(pairs.items(), key=lambda x: (x[1], x[0]))[0]
            
            if pairs[best_pair] < 2:
                break
            
            # Add to merges
            self.merges.append(best_pair)
            
            # Merge the pair in all tokens
            new_token_freqs = {}
            bigram = " ".join(best_pair)
            replacement = "".join(best_pair)
            
            for token, freq in token_freqs.items():
                new_token = token.replace(bigram, replacement)
                new_token_freqs[new_token] = freq
            
            token_freqs = new_token_freqs
            
            # Add new token to vocabulary
            new_token_str = "".join(best_pair)
            if new_token_str not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token_str] = new_id
                self.id_to_token[new_id] = new_token_str
    
    def encode(self, text: str) -> List[int]:
        text = unicodedata.normalize('NFKC', text)
        words = text.split()
        ids = []
        
        for word in words:
            tokens = list(word)
            
            # Apply all merge rules
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
            
            # Convert to IDs
            for token in tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    # Handle unknown tokens
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
            'special_tokens': self.special_tokens
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.special_tokens = data['special_tokens']
        self.id_to_token = {v: k for k, v in self.vocab.items()}
