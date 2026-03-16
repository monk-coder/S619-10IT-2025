#!/usr/bin/env python3
"""
Скрипт для анализа работы BPE токенизатора и экспериментов.
"""

import argparse
import os
import sys
import json
import matplotlib.pyplot as plt
from typing import List, Dict
import numpy as np

# Добавляем путь к текущей директории для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenizer import BPETokenizer


def compute_metrics(tokenizer: BPETokenizer, corpus: List[str]) -> Dict:
    """
    Вычисление метрик токенизатора на корпусе.

    Args:
        tokenizer: Токенизатор
        corpus: Корпус для оценки

    Returns:
        Словарь с метриками
    """
    print(f"Вычисление метрик на {len(corpus)} примерах...")

    lengths = []
    all_correct = True

    for i, text in enumerate(corpus):
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        lengths.append(len(ids))

        if text != decoded:
            all_correct = False

        if (i + 1) % 100 == 0:
            print(f"  Обработано {i + 1}/{len(corpus)}...")

    # Базовые метрики
    avg_length = np.mean(lengths)
    min_length = np.min(lengths)
    max_length = np.max(lengths)
    std_length = np.std(lengths)

    # Доля очень длинных токенизаций (top-1%)
    percentile_99 = np.percentile(lengths, 99)
    long_sequences = [l for l in lengths if l > percentile_99]
    long_percent = len(long_sequences) / len(lengths) * 100

    # Распределение длин
    hist, bins = np.histogram(lengths, bins=50)

    metrics = {
        'avg_length': float(avg_length),
        'min_length': int(min_length),
        'max_length': int(max_length),
        'std_length': float(std_length),
        'long_percent': float(long_percent),
        'perfect_reconstruction': all_correct,
        'percentile_99': float(percentile_99),
        'lengths_distribution': {
            'hist': hist.tolist(),
            'bins': bins.tolist()
        }
    }

    return metrics


def run_experiment(train_corpus: List[str], val_corpus: List[str],
                   merge_counts: List[int]) -> List[Dict]:
    """
    Проведение эксперимента с разным количеством слияний.

    Args:
        train_corpus: Обучающий корпус
        val_corpus: Валидационный корпус
        merge_counts: Список значений num_merges для тестирования

    Returns:
        Список результатов для каждого значения num_merges
    """
    results = []

    for num_merges in merge_counts:
        print(f"\n" + "=" * 60)
        print(f"Эксперимент с num_merges = {num_merges}")
        print("=" * 60)

        # Создаем и обучаем токенизатор
        tokenizer = BPETokenizer(num_merges=num_merges)
        tokenizer.train(train_corpus, verbose=False)

        # Вычисляем метрики
        metrics = compute_metrics(tokenizer, val_corpus)

        # Сохраняем результаты
        result = {
            'num_merges': num_merges,
            'vocab_size': tokenizer.get_vocab_size(),
            **metrics
        }

        results.append(result)

        # Выводим краткие результаты
        print(f"\nРезультаты для num_merges = {num_merges}:")
        print(f"  Размер словаря: {result['vocab_size']}")
        print(f"  Средняя длина: {result['avg_length']:.2f}")
        print(f"  Доля длинных (top-1%): {result['long_percent']:.2f}%")
        print(f"  Идеальное восстановление: {'Да' if result['perfect_reconstruction'] else 'Нет'}")

    return results


def plot_results(results: List[Dict], output_dir: str):
    """
    Визуализация результатов эксперимента.

    Args:
        results: Результаты экспериментов
        output_dir: Директория для сохранения графиков
    """
    os.makedirs(output_dir, exist_ok=True)

    # Подготовка данных
    merges = [r['num_merges'] for r in results]
    vocab_sizes = [r['vocab_size'] for r in results]
    avg_lengths = [r['avg_length'] for r in results]
    long_percents = [r['long_percent'] for r in results]

    # Создаем графики
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Размер словаря vs количество слияний
    axes[0, 0].plot(merges, vocab_sizes, 'bo-', linewidth=2)
    axes[0, 0].set_xlabel('Количество слияний')
    axes[0, 0].set_ylabel('Размер словаря')
    axes[0, 0].set_title('Размер словаря в зависимости от количества слияний')
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Средняя длина vs количество слияний
    axes[0, 1].plot(merges, avg_lengths, 'ro-', linewidth=2)
    axes[0, 1].set_xlabel('Количество слияний')
    axes[0, 1].set_ylabel('Средняя длина (токены)')
    axes[0, 1].set_title('Средняя длина токенизации')
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Доля длинных последовательностей vs количество слияний
    axes[1, 0].plot(merges, long_percents, 'go-', linewidth=2)
    axes[1, 0].set_xlabel('Количество слияний')
    axes[1, 0].set_ylabel('Доля длинных (%)')
    axes[1, 0].set_title('Доля очень длинных токенизаций (top-1%)')
    axes[1, 0].grid(True, alpha=0.3)

    # 4. Сравнение размера словаря и средней длины
    ax2 = axes[1, 1]
    color = 'tab:blue'
    ax2.set_xlabel('Количество слияний')
    ax2.set_ylabel('Размер словаря', color=color)
    ax2.plot(merges, vocab_sizes, color=color, linewidth=2)
    ax2.tick_params(axis='y', labelcolor=color)

    ax2_twin = ax2.twinx()
    color = 'tab:red'
    ax2_twin.set_ylabel('Средняя длина', color=color)
    ax2_twin.plot(merges, avg_lengths, color=color, linewidth=2, linestyle='--')
    ax2_twin.tick_params(axis='y', labelcolor=color)

    axes[1, 1].set_title('Размер словаря и средняя длина')

    plt.tight_layout()

    # Сохраняем графики
    plot_path = os.path.join(output_dir, 'bpe_analysis.png')
    plt.savefig(plot_path, dpi=150)
    print(f"\nГрафики сохранены в: {plot_path}")

    # Создаем график распределения длин для каждого эксперимента
    fig2, axes2 = plt.subplots(1, len(results), figsize=(15, 5))

    if len(results) == 1:
        axes2 = [axes2]

    for i, result in enumerate(results):
        ax = axes2[i]
        hist = result['lengths_distribution']['hist']
        bins = result['lengths_distribution']['bins']

        ax.bar(bins[:-1], hist, width=np.diff(bins), alpha=0.7)
        ax.set_xlabel('Длина последовательности')
        ax.set_ylabel('Частота')
        ax.set_title(f'num_merges = {result["num_merges"]}\n'
                     f'Средняя: {result["avg_length"]:.1f}')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    dist_plot_path = os.path.join(output_dir, 'length_distributions.png')
    plt.savefig(dist_plot_path, dpi=150)
    print(f"Графики распределений сохранены в: {dist_plot_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Анализ BPE токенизатора')
    parser.add_argument('--input_file', type=str, default='data.txt',
                        help='Файл с корпусом (по умолчанию: data.txt)')
    parser.add_argument('--merges_list', type=int, nargs='+',
                        default=[0, 500, 2000, 8000],
                        help='Список значений num_merges для тестирования')
    parser.add_argument('--output_dir', type=str, default='./analysis',
                        help='Директория для сохранения результатов')
    parser.add_argument('--val_split', type=float, default=0.1,
                        help='Доля данных для валидации')
    parser.add_argument('--seed', type=int, default=42,
                        help='Seed для воспроизводимости')

    args = parser.parse_args()

    # Устанавливаем seed
    np.random.seed(args.seed)

    # Создаем директорию для результатов
    os.makedirs(args.output_dir, exist_ok=True)

    # Читаем корпус
    print("Чтение корпуса...")
    with open(args.input_file, 'r', encoding='utf-8') as f:
        corpus = [line.strip() for line in f if line.strip()]

    print(f"Размер корпуса: {len(corpus)} строк")

    # Разделяем на train/val
    n_total = len(corpus)
    n_val = int(n_total * args.val_split)
    indices = np.random.permutation(n_total)

    train_indices = indices[n_val:]
    val_indices = indices[:n_val]

    train_corpus = [corpus[i] for i in train_indices]
    val_corpus = [corpus[i] for i in val_indices]

    print(f"Обучающая выборка: {len(train_corpus)} строк")
    print(f"Валидационная выборка: {len(val_corpus)} строк")

    # Проводим эксперимент
    print(f"\nЗапуск экспериментов с параметрами: {args.merges_list}")
    results = run_experiment(train_corpus, val_corpus, args.merges_list)

    # Сохраняем результаты
    results_path = os.path.join(args.output_dir, 'experiment_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты экспериментов сохранены в: {results_path}")

    # Создаем таблицу сравнения
    print("\n" + "=" * 80)
    print("ТАБЛИЦА СРАВНЕНИЯ РЕЗУЛЬТАТОВ")
    print("=" * 80)
    print(f"{'Слияния':<10} {'Словарь':<10} {'Ср. длина':<12} {'Длина σ':<10} {'Длинных%':<10} {'Восстановление':<15}")
    print("-" * 80)

    for result in results:
        print(f"{result['num_merges']:<10} "
              f"{result['vocab_size']:<10} "
              f"{result['avg_length']:<12.2f} "
              f"{result['std_length']:<10.2f} "
              f"{result['long_percent']:<10.2f} "
              f"{'✓' if result['perfect_reconstruction'] else '✗':<15}")

    print("=" * 80)

    # Создаем визуализации
    print("\nСоздание визуализаций...")
    plot_results(results, args.output_dir)

    # Анализ примеров для разных настроек
    print("\n" + "=" * 80)
    print("АНАЛИЗ ПРИМЕРОВ ТОКЕНИЗАЦИИ")
    print("=" * 80)

    # Берем несколько примеров из валидации
    sample_texts = val_corpus[:3]

    for i, text in enumerate(sample_texts):
        print(f"\nПример {i + 1}:")
        print(f"Текст: {text[:100]}..." if len(text) > 100 else f"Текст: {text}")

        for result in results:
            # Создаем токенизатор с соответствующим количеством слияний
            tokenizer = BPETokenizer(num_merges=result['num_merges'])
            tokenizer.train(train_corpus, verbose=False)

            ids = tokenizer.encode(text)
            decoded = tokenizer.decode(ids)

            print(f"\n  num_merges={result['num_merges']}:")
            print(f"    Длина: {len(ids)} токенов")
            print(f"    Первые 10 ID: {ids[:10]}" + ("..." if len(ids) > 10 else ""))
            print(f"    Совпадение: {'✓' if text == decoded else '✗'}")

            # Показываем некоторые токены
            if len(ids) > 0:
                sample_tokens = []
                for id_ in ids[:5]:
                    if id_ in tokenizer.vocab:
                        token = tokenizer.vocab[id_].replace('Ġ', '[SPACE]')
                        sample_tokens.append(f"'{token}'")
                    else:
                        sample_tokens.append('<UNK>')
                print(f"    Примеры токенов: {', '.join(sample_tokens)}")

    print("\n" + "=" * 80)
    print("Эксперимент завершен!")
    print(f"Все результаты сохранены в директории: {args.output_dir}")


if __name__ == '__main__':
    main()