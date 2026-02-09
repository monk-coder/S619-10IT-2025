import json
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import numpy as np
from tqdm import tqdm


class BPETokenizer:
    """BPE Tokenizer implementation from scratch."""
    
    def __init__(self, vocab_size: Optional[int] = None):
        """Initialize BPE Tokenizer.
        
        Args:
            vocab_size: Vocabulary size (if None, determined by num_merges)
        """
        self.vocab: Dict[str, int] = {}  # token -> id
        self.id_to_token: Dict[int, str] = {}  # id -> token
        self.merges: List[Tuple[str, str]] = []  # merge rules
        self.vocab_size = vocab_size
        self.special_tokens = {"<unk>": 0, "<pad>": 1, "<s>": 2, "</s>": 3}
        
    def _get_stats(self, vocab: Dict[str, int]) -> Dict[Tuple[str, str], int]:
        """Get frequency of pairs of tokens."""
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs
    
    def _merge_vocab(self, pair: Tuple[str, str], vocab: Dict[str, int]) -> Dict[str, int]:
        """Merge pair in vocabulary."""
        new_vocab = {}
        bigram = " ".join(pair)
        replacement = "".join(pair)
        
        for word, freq in vocab.items():
            new_word = word.replace(bigram, replacement)
            new_vocab[new_word] = freq
            
        return new_vocab
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        """Train BPE tokenizer on corpus.
        
        Args:
            corpus: List of text strings
            num_merges: Number of merge operations
            verbose: Whether to show progress
        """
        # Step 1: Preprocess and get initial vocabulary
        vocab = defaultdict(int)
        
        if verbose:
            print("Preprocessing corpus...")
            
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            
            # Simple whitespace tokenization as base
            words = text.split()
            for word in words:
                if word:
                    # Start with characters separated by spaces
                    token = " ".join(list(word))
                    vocab[token] += 1
        
        # Initialize with all characters
        chars = set()
        for word in vocab.keys():
            chars.update(word.split())
        
        # Build initial vocabulary
        sorted_chars = sorted(chars)
        self.vocab = {char: i + len(self.special_tokens) for i, char in enumerate(sorted_chars)}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Initial vocabulary size: {len(self.vocab)}")
            print(f"Starting {num_merges} merge operations...")
        
        # Step 2: Perform BPE merges
        for i in range(num_merges):
            # Get frequencies of all pairs
            pairs = self._get_stats(vocab)
            
            if not pairs:
                if verbose:
                    print(f"No more pairs to merge at step {i}")
                break
            
            # Find most frequent pair
            best_pair = max(pairs.items(), key=lambda x: (x[1], x[0]))[0]
            best_freq = pairs[best_pair]
            
            if best_freq < 2:
                if verbose:
                    print(f"All pairs have frequency < 2 at step {i}")
                break
            
            # Record the merge
            self.merges.append(best_pair)
            
            # Update vocabulary
            vocab = self._merge_vocab(best_pair, vocab)
            
            # Add new token to vocab
            new_token = "".join(best_pair)
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
        
        self.vocab_size = len(self.vocab)
        
        if verbose:
            print(f"Training completed. Vocabulary size: {self.vocab_size}")
            print(f"Number of merges performed: {len(self.merges)}")
    
    def _tokenize_word(self, word: str) -> List[str]:
        """Tokenize a single word using learned BPE merges."""
        # Start with characters
        tokens = list(word)
        
        # Apply all merge rules
        for pair in self.merges:
            new_tokens = []
            i = 0
            while i < len(tokens):
                # Check if we can merge this token with the next one
                if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                    new_tokens.append(pair[0] + pair[1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            
            # If we made any merges, continue with the new tokens
            if len(new_tokens) < len(tokens):
                tokens = new_tokens
            else:
                # No more merges possible for this pair
                continue
        
        return tokens
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs.
        
        Args:
            text: Input text
            
        Returns:
            List of token IDs
        """
        text = unicodedata.normalize('NFKC', text)
        
        # Simple whitespace tokenization
        words = text.split()
        ids = []
        
        for word in words:
            # Tokenize the word with BPE
            tokens = self._tokenize_word(word)
            
            # Convert tokens to IDs
            for token in tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    # If token not in vocab, try to split into characters
                    for char in token:
                        if char in self.vocab:
                            ids.append(self.vocab[char])
                        else:
                            # Unknown character
                            ids.append(self.special_tokens["<unk>"])
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Decode token IDs back to text.
        
        Args:
            ids: List of token IDs
            
        Returns:
            Decoded text
        """
        tokens = []
        for token_id in ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append("<unk>")
        
        # ИСПРАВЛЕНИЕ: просто склеиваем все токены
        return "".join(tokens)
    
    def save(self, filepath: str):
        """Save tokenizer to file.
        
        Args:
            filepath: Path to save file
        """
        data = {
            'vocab': self.vocab,
            'merges': [list(pair) for pair in self.merges],
            'vocab_size': self.vocab_size,
            'special_tokens': self.special_tokens
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """Load tokenizer from file.
        
        Args:
            filepath: Path to load file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.vocab_size = data['vocab_size']
        self.special_tokens = data['special_tokens']
        self.id_to_token = {v: k for k, v in self.vocab.items()}
    
    def get_vocab(self) -> Dict[str, int]:
        """Get vocabulary dictionary.
        
        Returns:
            Dictionary mapping tokens to IDs
        """
        return self.vocab.copy()


def split_train_val(corpus: List[str], val_ratio: float = 0.1) -> Tuple[List[str], List[str]]:
    """Split corpus into train and validation sets.
    
    Args:
        corpus: List of text strings
        val_ratio: Ratio for validation set
        
    Returns:
        Tuple of (train_corpus, val_corpus)
    """
    # Shuffle the corpus
    shuffled = corpus.copy()
    np.random.shuffle(shuffled)
    
    # Split
    split_idx = int(len(shuffled) * (1 - val_ratio))
    train = shuffled[:split_idx]
    val = shuffled[split_idx:]
    
    return train, val


def calculate_metrics(tokenizer: BPETokenizer, val_corpus: List[str]) -> Dict:
    """Calculate metrics on validation corpus.
    
    Args:
        tokenizer: Trained tokenizer
        val_corpus: Validation corpus
        
    Returns:
        Dictionary with metrics
    """
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
    
    # Calculate top 1% threshold
    threshold = np.percentile(lengths_array, 99) if len(lengths_array) > 0 else 0
    
    metrics = {
        'vocab_size': tokenizer.vocab_size,
        'avg_length': float(np.mean(lengths_array)),
        'median_length': float(np.median(lengths_array)),
        'std_length': float(np.std(lengths_array)),
        'min_length': int(np.min(lengths_array)),
        'max_length': int(np.max(lengths_array)),
        'long_sequences_ratio': float(np.mean(lengths_array > threshold)),
        'long_threshold': float(threshold)
    }
    
    return metrics


def validate_decoding(tokenizer: BPETokenizer, val_corpus: List[str], max_samples: int = 100) -> bool:
    """Validate that decode(encode(text)) == text.
    
    Args:
        tokenizer: Tokenizer to validate
        val_corpus: Validation corpus
        max_samples: Maximum number of samples to test
        
    Returns:
        True if all tests pass
    """
    if not val_corpus:
        return True
    
    # Test on subset
    test_samples = min(max_samples, len(val_corpus))
    
    for i in range(test_samples):
        text = val_corpus[i]
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        
        if decoded != text:
            print(f"Decoding failed for sample {i}:")
            print(f"  Original: '{text}'")
            print(f"  Encoded IDs: {encoded}")
            print(f"  Decoded: '{decoded}'")
            return False
    
    return True
