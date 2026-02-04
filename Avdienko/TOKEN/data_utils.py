import numpy as np
from typing import List, Tuple
import random


def read_corpus(file_path: str, max_lines: int = None) -> List[str]:
    """Читает текстовый корпус из файла."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = []
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            lines.append(line.strip())
    return lines


def split_train_val(corpus: List[str], val_size: float = 0.1,
                    seed: int = 42) -> Tuple[List[str], List[str]]:
    """Разделяет корпус на обучающую и валидационную выборки."""
    random.seed(seed)
    corpus_shuffled = corpus.copy()
    random.shuffle(corpus_shuffled)

    split_idx = int(len(corpus_shuffled) * (1 - val_size))
    train_data = corpus_shuffled[:split_idx]
    val_data = corpus_shuffled[split_idx:]

    return train_data, val_data


def calculate_statistics(tokenizer, data: List[str]) -> dict:
    """Вычисляет статистику токенизации."""
    lengths = []
    for text in data:
        ids = tokenizer.encode(text)
        lengths.append(len(ids))

    lengths = np.array(lengths)

    stats = {
        'mean_length': float(np.mean(lengths)),
        'median_length': float(np.median(lengths)),
        'std_length': float(np.std(lengths)),
        'max_length': int(np.max(lengths)),
        'min_length': int(np.min(lengths)),
        'p95_length': float(np.percentile(lengths, 95)),
        'p99_length': float(np.percentile(lengths, 99)),
        'total_tokens': int(np.sum(lengths)),
        'total_texts': len(data)
    }

    # Доля очень длинных токенизаций (top-1%)
    threshold = np.percentile(lengths, 99)
    long_ratio = np.sum(lengths >= threshold) / len(lengths)
    stats['long_sequences_ratio'] = float(long_ratio)

    return stats