import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from constants import SPECIAL_TOKENS, WORD_END_MARKER, WORD_PATTERN


class BPETokenizer:
    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.merges: Dict[Tuple[str, str], str] = {}
        self.inverse_vocab: Dict[int, str] = {}
        self.special_tokens = SPECIAL_TOKENS.copy()
        self.word_end_marker = WORD_END_MARKER
        self._compiled_pattern = re.compile(WORD_PATTERN)
    
    @staticmethod
    def _preprocess_text(text: str, pattern, word_end_marker) -> List[str]:
        words = []
        for match in pattern.finditer(text):
            word = match.group()
            if word.strip():
                words.append(word + word_end_marker)
        return words
    
    @staticmethod
    def _get_pairs(word: Tuple[str, ...]) -> Dict[Tuple[str, str], int]:
        pairs = defaultdict(int)
        for i in range(len(word) - 1):
            pair = (word[i], word[i + 1])
            pairs[pair] += 1
        return pairs
    
    def train(self, corpus: List[str], num_merges: int = 5000, verbose: bool = False) -> None:
        word_freqs = defaultdict(int)
        for text in corpus:
            words = self._preprocess_text(text, self._compiled_pattern, self.word_end_marker)
            for word in words:
                chars = tuple(word)
                word_freqs[chars] += 1
        
        if verbose:
            print(f"Unique words in corpus: {len(word_freqs)}")
        
        vocab = set()
        for word, freq in word_freqs.items():
            for char in word:
                vocab.add(char)
        
        self.merges = {}
        
        try:
            from tqdm import tqdm
            progress = tqdm(range(num_merges), desc="BPE Training") if verbose else range(num_merges)
        except ImportError:
            progress = range(num_merges)
            if verbose:
                print("tqdm not installed, training without progress bar")
        
        for i in progress:
            pair_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                pairs = self._get_pairs(word)
                for pair, count in pairs.items():
                    pair_freqs[pair] += count * freq
            
            if not pair_freqs:
                if verbose:
                    print(f"Stopped early at merge {i}: no more pairs to merge")
                break
            
            best_pair = max(pair_freqs, key=pair_freqs.get)
            new_token = ''.join(best_pair)
            self.merges[best_pair] = new_token
            
            new_word_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                new_word = self._apply_merge_to_word(word, best_pair, new_token)
                new_word_freqs[new_word] += freq
            
            word_freqs = new_word_freqs
            vocab.add(new_token)
        
        self.vocab = {token: idx for idx, token in enumerate(self.special_tokens)}
        current_id = len(self.special_tokens)
        
        all_tokens = set()
        for pair, merged in self.merges.items():
            all_tokens.add(pair[0])
            all_tokens.add(pair[1])
            all_tokens.add(merged)
        
        all_tokens.update(vocab)
        sorted_tokens = sorted(all_tokens, key=lambda x: (len(x), x))
        
        for token in sorted_tokens:
            if token not in self.vocab:
                self.vocab[token] = current_id
                current_id += 1
        
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}
        
        if verbose:
            print(f"Vocabulary size after {num_merges} merges: {len(self.vocab)}")
    
    @staticmethod
    def _apply_merge_to_word(word: Tuple[str, ...], pair: Tuple[str, str], new_token: str) -> Tuple[str, ...]:
        result = []
        i = 0
        while i < len(word):
            if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                result.append(new_token)
                i += 2
            else:
                result.append(word[i])
                i += 1
        return tuple(result)
    
    def _encode_word(self, word: str) -> List[str]:
        tokens = list(word)
        
        while True:
            pairs = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
            best_pair = None
            
            for pair in pairs:
                if pair in self.merges:
                    best_pair = pair
                    break
            
            if best_pair is None:
                break
            
            new_token = self.merges[best_pair]
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == best_pair[0] and tokens[i + 1] == best_pair[1]:
                    new_tokens.append(new_token)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        
        return tokens
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        if not self.vocab:
            raise RuntimeError("Tokenizer not trained yet. Call train() first.")
        
        words = self._preprocess_text(text, self._compiled_pattern, self.word_end_marker)
        tokens = []
        
        for word in words:
            word_tokens = self._encode_word(word)
            tokens.extend(word_tokens)
        
        ids = []
        if add_special_tokens:
            ids.append(self.vocab["<BOS>"])
        
        for token in tokens:
            ids.append(self.vocab.get(token, self.vocab["<UNK>"]))
        
        if add_special_tokens:
            ids.append(self.vocab["<EOS>"])
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        if not self.inverse_vocab:
            raise RuntimeError("Tokenizer not trained yet. Call train() first.")
        
        tokens = []
        for idx in ids:
            if idx in self.inverse_vocab:
                token = self.inverse_vocab[idx]
                if skip_special_tokens and token in self.special_tokens:
                    continue
                tokens.append(token)
        
        text = ''.join(tokens)
        text = text.replace(self.word_end_marker, '')
        
        return text
    
    def save(self, path: str) -> None:
        state = {
            "vocab": self.vocab,
            "merges": {f"{pair[0]},{pair[1]}": merged for pair, merged in self.merges.items()},
            "special_tokens": self.special_tokens,
            "word_end_marker": self.word_end_marker,
            "pat_str": WORD_PATTERN
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load(self, path: str) -> None:
        with open(path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        self.vocab = state["vocab"]
        self.merges = {tuple(pair.split(',')): merged for pair, merged in state["merges"].items()}
        self.special_tokens = state.get("special_tokens", SPECIAL_TOKENS)
        self.word_end_marker = state.get("word_end_marker", WORD_END_MARKER)
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}
        pat_str = state.get("pat_str", WORD_PATTERN)
        self._compiled_pattern = re.compile(pat_str)
    
    def get_vocab_size(self) -> int:
        return len(self.vocab)