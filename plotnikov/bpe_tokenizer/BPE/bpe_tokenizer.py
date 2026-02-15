import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


class BPETokenizer:
    """
    Byte Pair Encoding (BPE) tokenizer implementation from scratch.
    Based on Sennrich et al. "Neural Machine Translation of Rare Words with Subword Units"
    """
    
    def __init__(self):
        self.vocab: Dict[str, int] = {}          # token -> id mapping
        self.merges: Dict[Tuple[str, str], str] = {}  # (pair) -> merged token
        self.inverse_vocab: Dict[int, str] = {}  # id -> token mapping
        self.special_tokens = {"<PAD>": 0, "<UNK>": 1, "<BOS>": 2, "<EOS>": 3}
        self.word_end_marker = "</w>"
        # Используем стандартный re вместо regex для совместимости
        # Паттерн для разделения текста на слова/токены
        self._pat_str = r"'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+"
        self._compiled_pattern = re.compile(self._pat_str)
    
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Split text into space-separated words with end-of-word markers.
        """
        words = []
        for match in self._compiled_pattern.finditer(text):
            word = match.group()
            if word.strip():  # skip empty strings
                # Add space prefix if present, then strip spaces and add word end marker
                if word.startswith(' '):
                    word = word[1:] + self.word_end_marker
                else:
                    word = word + self.word_end_marker
                words.append(word)
        return words
    
    def _get_pairs(self, word: Tuple[str, ...]) -> Dict[Tuple[str, str], int]:
        """
        Get all adjacent symbol pairs in a word with their counts.
        """
        pairs = defaultdict(int)
        for i in range(len(word) - 1):
            pair = (word[i], word[i + 1])
            pairs[pair] += 1
        return pairs
    
    def train(self, corpus: List[str], num_merges: int = 10000, verbose: bool = False) -> None:
        """
        Train BPE tokenizer on corpus.
        
        Args:
            corpus: List of text documents
            num_merges: Number of merge operations to perform
            verbose: Whether to print progress
        """
        # Step 1: Preprocess corpus and count word frequencies
        word_freqs = defaultdict(int)
        for text in corpus:
            words = self._preprocess_text(text)
            for word in words:
                # Split word into characters + end marker
                chars = tuple(word)
                word_freqs[chars] += 1
        
        if verbose:
            print(f"Unique words in corpus: {len(word_freqs)}")
        
        # Step 2: Build initial vocabulary from all characters
        vocab = set()
        for word, freq in word_freqs.items():
            for char in word:
                vocab.add(char)
        
        # Initialize merges dictionary
        self.merges = {}
        
        # Step 3: Iterative merging
        try:
            from tqdm import tqdm
            progress = tqdm(range(num_merges), desc="BPE Training") if verbose else range(num_merges)
        except ImportError:
            progress = range(num_merges)
            if verbose:
                print("tqdm not installed, training without progress bar")
        
        for i in progress:
            # Count all pairs across the corpus
            pair_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                pairs = self._get_pairs(word)
                for pair, count in pairs.items():
                    pair_freqs[pair] += count * freq
            
            if not pair_freqs:
                if verbose:
                    print(f"Stopped early at merge {i}: no more pairs to merge")
                break
            
            # Find most frequent pair
            best_pair = max(pair_freqs, key=pair_freqs.get)
            new_token = ''.join(best_pair)
            
            # Store merge rule
            self.merges[best_pair] = new_token
            
            # Apply merge to all words in vocabulary
            new_word_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                new_word = self._apply_merge_to_word(word, best_pair, new_token)
                new_word_freqs[new_word] += freq
            
            word_freqs = new_word_freqs
            
            # Add new token to vocab set (will be added to final vocab later)
            vocab.add(new_token)
        
        # Step 4: Build final vocabulary with IDs
        # Start with special tokens
        self.vocab = {token: idx for idx, token in enumerate(self.special_tokens)}
        current_id = len(self.special_tokens)
        
        # Add all tokens from merges and initial characters
        all_tokens = set()
        for pair, merged in self.merges.items():
            all_tokens.add(pair[0])
            all_tokens.add(pair[1])
            all_tokens.add(merged)
        
        # Also add any remaining characters from initial vocab
        all_tokens.update(vocab)
        
        # Sort tokens for deterministic ordering (shorter first, then lexicographically)
        sorted_tokens = sorted(all_tokens, key=lambda x: (len(x), x))
        
        for token in sorted_tokens:
            if token not in self.vocab:
                self.vocab[token] = current_id
                current_id += 1
        
        # Build inverse mapping
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}
        
        if verbose:
            print(f"Vocabulary size after {num_merges} merges: {len(self.vocab)}")
    
    def _apply_merge_to_word(self, word: Tuple[str, ...], pair: Tuple[str, str], new_token: str) -> Tuple[str, ...]:
        """
        Apply a single merge operation to a word.
        """
        result = []
        i = 0
        while i < len(word):
            # Check if we can merge at position i
            if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                result.append(new_token)
                i += 2
            else:
                result.append(word[i])
                i += 1
        return tuple(result)
    
    def _encode_word(self, word: str) -> List[str]:
        """
        Encode a single word (with </w> marker) into subword tokens using learned merges.
        """
        # Start with character-level tokens
        tokens = list(word)
        
        # Iteratively apply merges as long as possible
        while True:
            # Find all pairs in current token sequence
            pairs = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
            
            # Find the first valid pair that has a merge rule
            best_pair = None
            for pair in pairs:
                if pair in self.merges:
                    best_pair = pair
                    break
            
            if best_pair is None:
                break
            
            # Apply the merge
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
        """
        Encode text into list of token IDs.
        
        Args:
            text: Input text string
            add_special_tokens: Whether to add <BOS> and <EOS> tokens
            
        Returns:
            List of token IDs
        """
        if not self.vocab:
            raise RuntimeError("Tokenizer not trained yet. Call train() first.")
        
        # Preprocess text into words
        words = self._preprocess_text(text)
        
        # Encode each word into subword tokens
        tokens = []
        for word in words:
            word_tokens = self._encode_word(word)
            tokens.extend(word_tokens)
        
        # Convert tokens to IDs
        ids = []
        if add_special_tokens:
            ids.append(self.vocab["<BOS>"])
        
        for token in tokens:
            ids.append(self.vocab.get(token, self.vocab["<UNK>"]))
        
        if add_special_tokens:
            ids.append(self.vocab["<EOS>"])
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode list of token IDs back to text.
        
        Args:
            ids: List of token IDs
            skip_special_tokens: Whether to skip special tokens in output
            
        Returns:
            Reconstructed text string
        """
        if not self.inverse_vocab:
            raise RuntimeError("Tokenizer not trained yet. Call train() first.")
        
        tokens = []
        for idx in ids:
            if idx in self.inverse_vocab:
                token = self.inverse_vocab[idx]
                if skip_special_tokens and token in self.special_tokens:
                    continue
                tokens.append(token)
        
        # Reconstruct text from tokens
        text = ''.join(tokens)
        
        # Remove word end markers and handle spaces
        text = text.replace(self.word_end_marker, ' ')
        
        # Clean up multiple spaces and leading/trailing spaces
        text = re.sub(r' +', ' ', text).strip()
        
        # Handle punctuation spacing (remove space before punctuation)
        text = re.sub(r' ([^\w\s])', r'\1', text)
        # Fix space after punctuation when followed by space
        text = re.sub(r'([^\w\s]) ', r'\1 ', text)
        
        return text
    
    def save(self, path: str) -> None:
        """
        Save tokenizer state to file.
        """
        state = {
            "vocab": self.vocab,
            "merges": {f"{pair[0]},{pair[1]}": merged for pair, merged in self.merges.items()},
            "special_tokens": self.special_tokens,
            "word_end_marker": self.word_end_marker,
            "pat_str": self._pat_str
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load(self, path: str) -> None:
        """
        Load tokenizer state from file.
        """
        with open(path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        self.vocab = state["vocab"]
        self.merges = {tuple(pair.split(',')): merged for pair, merged in state["merges"].items()}
        self.special_tokens = state.get("special_tokens", {"<PAD>": 0, "<UNK>": 1, "<BOS>": 2, "<EOS>": 3})
        self.word_end_marker = state.get("word_end_marker", "</w>")
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}
        pat_str = state.get("pat_str", r"'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+")
        self._compiled_pattern = re.compile(pat_str)
    
    def get_vocab_size(self) -> int:
        """Return vocabulary size."""
        return len(self.vocab)