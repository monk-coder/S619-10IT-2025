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
        """Initialize BPE Tokenizer.
        
        Args:
            vocab_size: Vocabulary size (if None, determined by num_merges)
        """
        self.vocab: Dict[str, int] = {}  # token -> id
        self.id_to_token: Dict[int, str] = {}  # id -> token
        self.merges: List[Tuple[str, str]] = []  # merge rules
        self.vocab_size = vocab_size
        self.special_tokens = {"<unk>": 0, "<pad>": 1, "<s>": 2, "</s>": 3}
        # Исправляем паттерн для корректной работы с Unicode
        self.pattern = re.compile(
            r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""",
            re.IGNORECASE | re.UNICODE
        )
        
    def _get_stats(self, token_freqs: Dict[str, int]) -> Dict[Tuple[str, str], int]:
        """Calculate frequencies of adjacent token pairs.
        
        Args:
            token_freqs: Dictionary with token frequencies
            
        Returns:
            Dictionary with pair frequencies
        """
        pairs = defaultdict(int)
        for token, freq in token_freqs.items():
            symbols = token.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs
    
    def _merge_pair(self, pair: Tuple[str, str], token_freqs: Dict[str, int]) -> Dict[str, int]:
        """Merge the most frequent pair of tokens.
        
        Args:
            pair: Token pair to merge
            token_freqs: Current token frequencies
            
        Returns:
            Updated token frequencies
        """
        new_token = pair[0] + pair[1]
        new_token_freqs = {}
        bigram = " ".join(pair)
        replacement = "".join(pair)
        
        for token, freq in token_freqs.items():
            new_token_str = token.replace(bigram, replacement)
            new_token_freqs[new_token_str] = freq
        
        return new_token_freqs
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        """Train BPE on corpus.
        
        Args:
            corpus: List of text strings
            num_merges: Number of merges to perform
            verbose: Whether to show progress
        """
        # Initialize character frequencies
        token_freqs = defaultdict(int)
        
        if verbose:
            print("Preprocessing text and counting character frequencies...")
        
        # Count word frequencies with pre-tokenization
        for text in tqdm(corpus, disable=not verbose, desc="Processing corpus"):
            text = unicodedata.normalize('NFKC', text)
            tokens = re.findall(self.pattern, text)
            for token in tokens:
                # Инициализируем как последовательность символов с пробелом между ними
                bpe_token = " ".join(list(token))
                token_freqs[bpe_token] += 1
        
        # Initialize base vocabulary
        chars = set()
        for token in token_freqs.keys():
            chars.update(token.split())
        
        # Сортируем символы для воспроизводимости
        sorted_chars = sorted(chars)
        self.vocab = {char: i + len(self.special_tokens) for i, char in enumerate(sorted_chars)}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        self.vocab_size = len(self.vocab)
        
        if verbose:
            print(f"Initialized base vocabulary with {len(chars)} characters")
            print(f"Initial vocabulary size: {self.vocab_size}")
            if num_merges > 0:
                print(f"Performing {num_merges} merges...")
        
        # Perform merges
        for i in tqdm(range(num_merges), disable=not verbose or num_merges == 0, desc="BPE merges"):
            pairs = self._get_stats(token_freqs)
            
            if not pairs:
                if verbose:
                    print(f"No pairs to merge at step {i}")
                break
            
            # Находим наиболее частую пару
            # Используем кортеж для стабильной сортировки при одинаковых частотах
            best_pair = max(pairs.items(), key=lambda x: (x[1], x[0]))[0]
            best_freq = pairs[best_pair]
            
            if best_freq < 2:
                if verbose:
                    print(f"All pairs occur < 2 times at step {i}")
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
            print(f"Training completed. Final vocabulary size: {self.vocab_size}")
            print(f"Merges performed: {len(self.merges)}")
    
    def _apply_merges(self, word: str) -> List[str]:
        """Apply all merge rules to a word.
        
        Args:
            word: Input word
            
        Returns:
            List of BPE tokens
        """
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
        """Encode text to token IDs.
        
        Args:
            text: Input text
            
        Returns:
            List of token IDs
        """
        text = unicodedata.normalize('NFKC', text)
        words = re.findall(self.pattern, text)
        
        ids = []
        for word in words:
            bpe_tokens = self._apply_merges(word)
            
            for token in bpe_tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    # Если токен не найден, разбиваем на символы
                    for char in token:
                        if char in self.vocab:
                            ids.append(self.vocab[char])
                        else:
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
        for id_ in ids:
            if id_ in self.id_to_token:
                tokens.append(self.id_to_token[id_])
            else:
                tokens.append("<unk>")
        
        text = "".join(tokens)
        # Восстанавливаем пробелы: добавляем пробел между токенами, которые не были слиты
        # Более простая и надежная логика
        text = re.sub(r'(?<=[^\s])(?=\p{L}|\p{N})', ' ', text)
        
        return text
    
    def save(self, filepath: str):
        """Save tokenizer to file.
        
        Args:
            filepath: Path to save file
        """
        # Конвертируем кортежи в списки для JSON сериализации
        serializable_merges = [list(pair) for pair in self.merges]
        
        data = {
            'vocab': self.vocab,
            'merges': serializable_merges,
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
        # Конвертируем списки обратно в кортежи
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
        corpus: Full corpus
        val_ratio: Validation ratio
        
    Returns:
        Tuple of (train, val)
    """
    # Создаем копию, чтобы не менять оригинальный список
    shuffled = corpus.copy()
    np.random.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1 - val_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]


def calculate_metrics(tokenizer: BPETokenizer, val_corpus: List[str]) -> Dict:
    """Calculate metrics on validation corpus.
    
    Args:
        tokenizer: Trained tokenizer
        val_corpus: Validation corpus
        
    Returns:
        Dictionary with metrics
    """
    lengths = []
    all_ids = []
    
    for text in val_corpus:
        ids = tokenizer.encode(text)
        lengths.append(len(ids))
        all_ids.extend(ids)
    
    # Конвертируем в Python типы для JSON сериализации
    metrics = {
        'vocab_size': tokenizer.vocab_size,
        'avg_length': float(np.mean(lengths)) if lengths else 0.0,
        'median_length': float(np.median(lengths)) if lengths else 0.0,
        'std_length': float(np.std(lengths)) if len(lengths) > 1 else 0.0,
        'min_length': int(np.min(lengths)) if lengths else 0,
        'max_length': int(np.max(lengths)) if lengths else 0,
        'total_tokens': len(all_ids),
        'unique_tokens': len(set(all_ids))
    }
    
    # Доля очень длинных токенизаций (top-1%)
    if lengths:
        lengths_array = np.array(lengths)
        threshold = np.percentile(lengths_array, 99)
        long_ratio = np.mean(lengths_array > threshold)
        metrics['long_sequences_ratio'] = float(long_ratio)
        metrics['long_threshold'] = float(threshold)
    else:
        metrics['long_sequences_ratio'] = 0.0
        metrics['long_threshold'] = 0.0
    
    return metrics


def validate_decoding(tokenizer: BPETokenizer, val_corpus: List[str], num_samples: int = 100) -> bool:
    """Validate that decode(encode(text)) == text.
    
    Args:
        tokenizer: Tokenizer to validate
        val_corpus: Validation corpus
        num_samples: Number of samples to test
        
    Returns:
        True if all tests pass
    """
    if not val_corpus:
        print("Warning: Validation corpus is empty")
        return True
    
    samples = min(num_samples, len(val_corpus))
    
    for i in range(samples):
        text = val_corpus[i]
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        
        if decoded != text:
            print(f"Decoding failed for sample {i}:")
            print(f"  Original: {text[:100]}...")
            print(f"  Decoded:  {decoded[:100]}...")
            print(f"  Original length: {len(text)}")
            print(f"  Decoded length: {len(decoded)}")
            print(f"  Encoded IDs: {encoded}")
            return False
    
    return True
