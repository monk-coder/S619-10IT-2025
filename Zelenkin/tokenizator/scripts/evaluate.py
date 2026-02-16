#!/usr/bin/env python
"""Скрипт для оценки и сравнения токенизаторов."""

import argparse
import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from src.tokenizer import BPETokenizer
from src.utils.data_loader import DataLoader
from src.utils.metrics import TokenizerMetrics
from src.visualization.plots import TokenizerVisualizer


def parse_args():
    parser = argparse.ArgumentParser(description='Оценка BPE токенизаторов')
    parser.add_argument('--models', type=str, nargs='+', required=True,
                        help='Пути к файлам моделей')
    parser.add_argument('--data', type=str, default='data/raw/data.txt',
                        help='Путь к файлу с данными')
    parser.add_argument('--output', type=str, default='results/evaluation',
                        help='Директория для сохранения результатов')
    return parser.parse_args()


def main():
    args = parse_args()

    # Создаем директорию для результатов
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Загрузка данных
    loader = DataLoader(args.data)
    corpus = loader.load_corpus()
    _, val_data = loader.train_val_split(corpus, val_size=0.1)

    # Загрузка моделей
    tokenizers = {}
    metrics_dict = {}
    lengths_dict = {}

    print("=" * 60)
    print("ЗАГРУЗКА МОДЕЛЕЙ")
    print("=" * 60)

    for model_path in args.models:
        name = Path(model_path).stem
        print(f"\nЗагрузка {name}...")

        tokenizer = BPETokenizer()
        tokenizer.load(model_path)
        tokenizers[name] = tokenizer

        # Вычисление метрик
        metrics_calc = TokenizerMetrics(tokenizer)
        lengths = metrics_calc.compute_lengths(val_data)
        stats = metrics_calc.get_statistics(val_data)

        metrics_dict[name] = stats
        lengths_dict[name] = lengths

        print(f"  Размер словаря: {stats['vocab_size']}")
        print(f"  Средняя длина: {stats['mean_length']:.2f}")
        print(f"  99-й перцентиль: {stats['p99_length']:.2f}")

    # Визуализация
    print("\n" + "=" * 60)
    print("ВИЗУАЛИЗАЦИЯ")
    print("=" * 60)

    visualizer = TokenizerVisualizer()

    # График распределения длин
    visualizer.plot_length_distribution(
        lengths_dict,
        save_path=output_dir / 'length_distribution.png'
    )

    # Добавляем длины для box plot
    for name in metrics_dict:
        metrics_dict[name]['lengths'] = lengths_dict[name]

    # График сравнения метрик
    visualizer.plot_metrics_comparison(
        metrics_dict,
        save_path=output_dir / 'metrics_comparison.png'
    )

    # Сохранение результатов в JSON
    results = {
        'metrics': {name: {k: v for k, v in stats.items() if k != 'lengths'}
                    for name, stats in metrics_dict.items()}
    }

    with open(output_dir / 'evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты сохранены в {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()