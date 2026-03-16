"""Метрики и статистика для анализа токенизатора."""

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter


class TokenizerMetrics:
    """Вычисление метрик токенизатора."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def compute_lengths(self, corpus: List[str]) -> np.ndarray:
        """
        Вычисление длин токенизации для корпуса.

        Args:
            corpus: список текстов

        Returns:
            массив длин
        """
        lengths = []
        for text in corpus:
            token_ids = self.tokenizer.encode(text)
            lengths.append(len(token_ids))
        return np.array(lengths)

    def get_statistics(self, corpus: List[str]) -> Dict[str, Any]:
        """
        Получение полной статистики.

        Args:
            corpus: корпус для анализа

        Returns:
            словарь со статистикой
        """
        lengths = self.compute_lengths(corpus)

        stats = {
            'vocab_size': self.tokenizer.vocab_size,
            'num_merges': self.tokenizer.merges_count,
            'total_texts': len(corpus),
            'mean_length': float(np.mean(lengths)),
            'std_length': float(np.std(lengths)),
            'median_length': float(np.median(lengths)),
            'min_length': int(np.min(lengths)),
            'max_length': int(np.max(lengths)),
            'p95_length': float(np.percentile(lengths, 95)),
            'p99_length': float(np.percentile(lengths, 99)),
            'total_tokens': int(np.sum(lengths)),
            'tokens_per_char': float(np.sum(lengths) / sum(len(t) for t in corpus))
        }

        return stats

    def get_token_frequencies(self, corpus: List[str]) -> Dict[str, int]:
        """
        Подсчет частот токенов в корпусе.

        Args:
            corpus: корпус для анализа

        Returns:
            словарь {токен: частота}
        """
        token_counter = Counter()

        for text in corpus:
            token_ids = self.tokenizer.encode(text)
            tokens = [self.tokenizer.vocab.id_to_token.get(id, '<UNK>')
                      for id in token_ids]
            token_counter.update(tokens)

        return dict(token_counter.most_common())

    def find_long_tokenizations(self, corpus: List[str], top_k: int = 10) -> List[Tuple[str, int]]:
        """
        Поиск самых длинных токенизаций.

        Args:
            corpus: корпус для анализа
            top_k: количество результатов

        Returns:
            список (текст, длина)
        """
        texts_with_lengths = []

        for text in corpus:
            length = len(self.tokenizer.encode(text))
            texts_with_lengths.append((text, length))

        texts_with_lengths.sort(key=lambda x: x[1], reverse=True)

        return texts_with_lengths[:top_k]