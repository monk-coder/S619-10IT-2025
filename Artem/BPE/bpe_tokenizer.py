import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional


class BPETokenizer:
    """
    Byte Pair Encoding tokenizer implemented from scratch.
    Based on Sennrich et al. "Neural Machine Translation of Rare Words with Subword Units"
    """
    
    def __init__(self, eos_token: str = "</w>"):
        self.eos_token = eos_token
        self.merges: Dict[Tuple[str, str], str] = {}  # (pair) -> merged token
        self.vocab: Dict[str, int] = {}               # token -> id
        self.inverse_vocab: Dict[int, str] = {}       # id -> token
    
    def _get_stats(self, tokens: List[str]) -> Counter:
        """Count frequency of adjacent token pairs."""
        pairs = Counter()
        for i in range(len(tokens) - 1):
            pairs[(tokens[i], tokens[i + 1])] += 1
        return pairs
    
    def _merge_tokens(self, tokens: List[str], pair: Tuple[str, str], merged_token: str) -> List[str]:
        """Apply a single merge operation to a token sequence."""
        if len(tokens) < 2:
            return tokens
        
        new_tokens = []
        i = 0
        while i < len(tokens):
            # Check if we can merge current and next token
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(merged_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens
    
    def train(self, corpus: List[str], num_merges: int = 10000, verbose: bool = True):
        """
        Train BPE tokenizer on a corpus.
        
        Args:
            corpus: List of text documents
            num_merges: Number of merge operations to perform
            verbose: Whether to show progress
        """
        # Step 1: Initialize vocabulary with character-level tokens + EOS markers
        tokenized_corpus = []
        char_freqs = Counter()
        
        for text in corpus:
            # Split into words, then into characters with EOS markers
            words = re.findall(r'\S+|\s+', text)  # preserve spaces as separate tokens
            tokenized_words = []
            for word in words:
                if word.strip():  # non-whitespace word
                    chars = list(word) + [self.eos_token]
                else:  # whitespace
                    chars = list(word)
                tokenized_words.extend(chars)
                char_freqs.update(chars)
            tokenized_corpus.append(tokenized_words)
        
        # Build initial character vocabulary
        sorted_chars = sorted(char_freqs.keys())
        self.vocab = {char: idx for idx, char in enumerate(sorted_chars)}
        current_vocab_size = len(self.vocab)
        
        # Step 2: Iterative merging
        from tqdm import tqdm
        merge_range = tqdm(range(num_merges), desc="BPE Merges") if verbose else range(num_merges)
        
        for i in merge_range:
            # Count all pairs in the current tokenized corpus
            pairs = Counter()
            for tokens in tokenized_corpus:
                pairs.update(self._get_stats(tokens))
            
            if not pairs:
                if verbose:
                    print(f"Stopped early at merge {i}/{num_merges}: no more pairs")
                break
            
            # Find the most frequent pair
            most_common_pair = pairs.most_common(1)[0][0]
            
            # Create merged token
            merged_token = most_common_pair[0] + most_common_pair[1].replace(self.eos_token, '')
            if most_common_pair[1].endswith(self.eos_token):
                merged_token += self.eos_token
            
            # Store merge rule
            self.merges[most_common_pair] = merged_token
            self.vocab[merged_token] = current_vocab_size
            current_vocab_size += 1
            
            # Apply merge to entire corpus for next iteration
            new_corpus = []
            for tokens in tokenized_corpus:
                new_corpus.append(self._merge_tokens(tokens, most_common_pair, merged_token))
            tokenized_corpus = new_corpus
        
        # Build inverse vocabulary
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}
        
        if verbose:
            print(f"Training complete. Vocabulary size: {len(self.vocab)}")
    
    def _tokenize_word(self, word: str) -> List[str]:
        """Split word into characters with EOS marker."""
        if not word.strip():
            return list(word)  # preserve whitespace as-is
        return list(word) + [self.eos_token]
    
    def _apply_merges(self, tokens: List[str]) -> List[str]:
        """Apply all learned merges greedily in order of creation."""
        # Optimization: process merges in batches by length
        # Simple approach: iterate until no merges possible
        while True:
            # Find all mergeable pairs in current token sequence
            possible_merges = []
            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                if pair in self.merges:
                    possible_merges.append((i, pair))
            
            if not possible_merges:
                break
            
            # Apply the earliest merge (leftmost)
            i, pair = min(possible_merges, key=lambda x: x[0])
            merged_token = self.merges[pair]
            
            # Replace the pair with merged token
            tokens = tokens[:i] + [merged_token] + tokens[i + 2:]
        
        return tokens
    
    def encode(self, text: str) -> List[int]:
        """Convert text to list of token IDs."""
        if not text:
            return []
        
        # Split text preserving whitespace boundaries
        words = re.findall(r'\S+|\s+', text)
        
        # Tokenize each word/whitespace segment
        all_tokens = []
        for word in words:
            if word.strip():  # actual word
                tokens = self._tokenize_word(word)
                tokens = self._apply_merges(tokens)
                all_tokens.extend(tokens)
            else:  # whitespace
                all_tokens.extend(list(word))
        
        # Convert tokens to IDs (fallback to character-level if unknown)
        ids = []
        for token in all_tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                # Fallback: split into characters (should not happen after proper training)
                for char in token.replace(self.eos_token, ''):
                    if char in self.vocab:
                        ids.append(self.vocab[char])
                if token.endswith(self.eos_token) and self.eos_token in self.vocab:
                    ids.append(self.vocab[self.eos_token])
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Convert token IDs back to text."""
        if not ids:
            return ""
        
        tokens = [self.inverse_vocab.get(idx, "") for idx in ids]
        
        # Reconstruct text from tokens
        text = ""
        for token in tokens:
            if token.endswith(self.eos_token):
                # Word token: remove EOS marker and add to text
                text += token[:-len(self.eos_token)]
            else:
                # Character or whitespace
                text += token
        
        return text
    
    def save(self, path: str):
        """Save tokenizer state to JSON file."""
        data = {
            "eos_token": self.eos_token,
            "merges": {f"{k[0]},{k[1]}": v for k, v in self.merges.items()},
            "vocab": self.vocab
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'BPETokenizer':
        """Load tokenizer state from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tokenizer = cls(eos_token=data["eos_token"])
        tokenizer.merges = {tuple(k.split(',')): v for k, v in data["merges"].items()}
        tokenizer.vocab = data["vocab"]
        tokenizer.inverse_vocab = {idx: token for token, idx in tokenizer.vocab.items()}
        
        return tokenizer
    
    def vocab_size(self) -> int:
        """Return current vocabulary size."""
        return len(self.vocab)