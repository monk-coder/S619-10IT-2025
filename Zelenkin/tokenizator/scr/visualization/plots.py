"""Визуализация результатов."""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional
import seaborn as sns


class TokenizerVisualizer:
    """Визуализация результатов работы токенизатора."""

    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        plt.style.use(style)

    def plot_length_distribution(
            self,
            lengths_dict: Dict[str, np.ndarray],
            save_path: Optional[str] = None
    ) -> None:
        """
        Построение распределения длин токенизации.

        Args:
            lengths_dict: словарь {название: массив длин}
            save_path: путь для сохранения
        """
        plt.figure(figsize=(12, 6))

        for name, lengths in lengths_dict.items():
            plt.hist(lengths, bins=50, alpha=0.5, label=name, density=True)

        plt.xlabel('Длина последовательности (токены)')
        plt.ylabel('Плотность')
        plt.title('Распределение длин токенизации')
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()

    def plot_metrics_comparison(
            self,
            metrics_dict: Dict[str, Dict],
            save_path: Optional[str] = None
    ) -> None:
        """
        Сравнение метрик для разных токенизаторов.

        Args:
            metrics_dict: словарь {название: метрики}
            save_path: путь для сохранения
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        names = list(metrics_dict.keys())

        # График 1: Размер словаря
        vocab_sizes = [metrics_dict[n]['vocab_size'] for n in names]
        axes[0].bar(names, vocab_sizes, color='skyblue')
        axes[0].set_xlabel('Токенизатор')
        axes[0].set_ylabel('Размер словаря')
        axes[0].set_title('Размер словаря')
        axes[0].tick_params(axis='x', rotation=45)

        # График 2: Средняя длина
        mean_lengths = [metrics_dict[n]['mean_length'] for n in names]
        axes[1].bar(names, mean_lengths, color='lightgreen')
        axes[1].set_xlabel('Токенизатор')
        axes[1].set_ylabel('Средняя длина')
        axes[1].set_title('Средняя длина токенизации')
        axes[1].tick_params(axis='x', rotation=45)

        # График 3: Box plot длин
        for i, name in enumerate(names):
            if 'lengths' in metrics_dict[name]:
                lengths = metrics_dict[name]['lengths']
                axes[2].boxplot(lengths, positions=[i], widths=0.6, labels=[name])

        axes[2].set_xlabel('Токенизатор')
        axes[2].set_ylabel('Длина')
        axes[2].set_title('Распределение длин')
        axes[2].tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()

    def plot_token_frequencies(
            self,
            frequencies: Dict[str, int],
            top_k: int = 20,
            save_path: Optional[str] = None
    ) -> None:
        """
        Построение частот токенов.

        Args:
            frequencies: словарь {токен: частота}
            top_k: количество токенов для отображения
            save_path: путь для сохранения
        """
        top_tokens = list(frequencies.items())[:top_k]
        tokens, counts = zip(*top_tokens)

        plt.figure(figsize=(12, 6))
        plt.bar(range(len(tokens)), counts)
        plt.xlabel('Токены')
        plt.ylabel('Частота')
        plt.title(f'Топ-{top_k} самых частых токенов')
        plt.xticks(range(len(tokens)), tokens, rotation=45, ha='right')

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()