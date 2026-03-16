import numpy as np
import random
from pathlib import Path
from typing import List, Tuple
from bpe_tokenizer import BPETokenizer


def load_corpus(path: str) -> List[str]:
    if not Path(path).exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    return lines


def create_dataset(tokenizer: BPETokenizer, corpus: List[str], seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
    all_tokens = []
    for text in corpus:
        tokens = tokenizer.encode(text)
        all_tokens.extend(tokens)
    
    n_samples = len(all_tokens) - seq_len
    if n_samples <= 0:
        raise ValueError(f"Corpus too small for sequence length {seq_len}")
    
    x = np.zeros((n_samples, seq_len), dtype=np.int32)
    y = np.zeros((n_samples, seq_len), dtype=np.int32)
    
    for i in range(n_samples):
        x[i] = all_tokens[i:i+seq_len]
        y[i] = all_tokens[i+1:i+seq_len+1]
    
    return x, y


def train_val_split(x: np.ndarray, y: np.ndarray, val_ratio: float = 0.1) -> Tuple:
    n_val = int(len(x) * val_ratio)
    indices = np.random.permutation(len(x))
    
    x_train = x[indices[n_val:]]
    y_train = y[indices[n_val:]]
    x_val = x[indices[:n_val]]
    y_val = y[indices[:n_val]]
    
    return x_train, y_train, x_val, y_val


def batch_generator(x: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool = True):
    n_samples = len(x)
    indices = np.arange(n_samples)
    
    if shuffle:
        np.random.shuffle(indices)
    
    for start_idx in range(0, n_samples, batch_size):
        batch_indices = indices[start_idx:start_idx + batch_size]
        yield x[batch_indices], y[batch_indices]


def top_k_logits(logits: np.ndarray, k: int) -> np.ndarray:
    if k == 0:
        return logits
    
    vals = np.partition(logits, -k, axis=-1)[:, -k]
    mask = logits < vals[:, None]
    logits[mask] = -np.inf
    return logits


def sample_next_token(logits: np.ndarray, temperature: float = 1.0, top_k: int = 0) -> int:
    logits = logits / temperature
    logits = top_k_logits(logits, top_k)
    
    probs = np.exp(logits - np.max(logits))
    probs = probs / np.sum(probs)
    
    return np.random.choice(len(probs), p=probs)