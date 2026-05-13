import json
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple

class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.id_to_token = {}
        self.merges = []
        self.special_tokens = {"<unk>": 0, "<pad>": 1}
        self.eos_token = "</s>"
        self.eos_token_id = None
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        all_chars = set()
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            for char in text:
                all_chars.add(char)
        all_chars.add(' ')
        
        char_list = sorted(list(all_chars))
        self.vocab = {}
        for i, char in enumerate(char_list):
            self.vocab[char] = i + 2
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose: print(f"Initial vocab size: {len(self.vocab)}")
        
        word_freqs = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    word_freqs[" ".join(list(word))] += 1
        
        if verbose: print(f"Unique words: {len(word_freqs)}")
        
        for i in range(num_merges):
            pair_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                symbols = word.split()
                for j in range(len(symbols) - 1):
                    pair_freqs[(symbols[j], symbols[j + 1])] += freq
            if not pair_freqs: break
            
            best_pair = max(pair_freqs.items(), key=lambda x: x[1])[0]
            best_freq = pair_freqs[best_pair]
            if best_freq < 2: break
            
            self.merges.append(best_pair)
            new_token = best_pair[0] + best_pair[1]
            if new_token not in self.vocab:
                self.vocab[new_token] = len(self.vocab)
                self.id_to_token[len(self.vocab) - 1] = new_token
            
            new_word_freqs = defaultdict(int)
            bigram = " ".join(best_pair)
            for word, freq in word_freqs.items():
                new_word_freqs[word.replace(bigram, new_token)] += freq
            word_freqs = new_word_freqs
            
            if verbose and (i + 1) % 500 == 0:
                print(f"  Merge {i+1}/{num_merges}: '{best_pair[0]}+{best_pair[1]}' (freq: {best_freq})")
                
        if verbose:
            print(f"Final vocab size: {len(self.vocab)}")
            print(f"Merges performed: {len(self.merges)}")
            
        # Совместимость с заданием 5
        if self.eos_token not in self.vocab:
            self.vocab[self.eos_token] = len(self.vocab)
            self.id_to_token[len(self.vocab) - 1] = self.eos_token
        self.eos_token_id = self.vocab[self.eos_token]
    
    def encode(self, text: str) -> List[int]:
        text = unicodedata.normalize('NFKC', text)
        words = text.split()
        ids = []
        for i, word in enumerate(words):
            if i > 0:
                ids.append(self.vocab.get(" ", 1))
            tokens = list(word)
            for pair in self.merges:
                new_tokens = []
                j = 0
                while j < len(tokens):
                    if j < len(tokens) - 1 and tokens[j] == pair[0] and tokens[j + 1] == pair[1]:
                        new_tokens.append(pair[0] + pair[1])
                        j += 2
                    else:
                        new_tokens.append(tokens[j])
                        j += 1
                tokens = new_tokens
            for token in tokens:
                ids.append(self.vocab.get(token, 0))
        return ids
    
    def decode(self, ids: List[int]) -> str:
        return "".join(self.id_to_token.get(tid, "<unk>") for tid in ids)
    
    def __len__(self):
        return len(self.vocab)
    
    def save(self, filepath: str):
        data = {
            'vocab': self.vocab,
            'merges': [list(pair) for pair in self.merges],
            'special_tokens': self.special_tokens,
            'eos_token': self.eos_token,
            'eos_token_id': self.eos_token_id
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    @classmethod
    def load(cls, filepath: str) -> 'BPETokenizer':
        obj = cls()
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        obj.vocab = {k: int(v) for k, v in data['vocab'].items()}
        obj.merges = [tuple(pair) for pair in data['merges']]
        obj.special_tokens = data.get('special_tokens', {"<unk>": 0, "<pad>": 1})
        obj.eos_token = data.get('eos_token', '</s>')
        obj.eos_token_id = data.get('eos_token_id', obj.vocab.get(obj.eos_token, len(obj.vocab) - 1))
        obj.id_to_token = {v: k for k, v in obj.vocab.items()}
        return obj
