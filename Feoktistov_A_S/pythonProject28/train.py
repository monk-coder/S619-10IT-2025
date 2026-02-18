#!/usr/bin/env python3
"""
Скрипт для обучения BPE токенизатора.
"""

import argparse
import os
import sys
from typing import List
import numpy as np

# Добавляем путь к текущей директории для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenizer import BPETokenizer


def read_corpus(filepath: str) -> List[str]:
    """
    Чтение корпуса из файла.

    Args:
        filepath: Путь к файлу с корпусом

    Returns:
        Список строк (документов)
    """
    print(f"Чтение корпуса из {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Прочитано {len(lines)} строк")
    return lines


def split_train_val(corpus: List[str], val_split: float = 0.1) -> tuple:
    """
    Разделение корпуса на обучающую и валидационную выборки.

    Args:
        corpus: Весь корпус
        val_split: Доля валидационной выборки

    Returns:
        Кортеж (train_corpus, val_corpus)
    """
    n_total = len(corpus)
    n_val = int(n_total * val_split)
    n_train = n_total - n_val

    # Перемешиваем корпус для случайного разбиения
    indices = np.random.permutation(n_total)

    train_indices = indices[:n_train]
    val_indices = indices[n_train:]

    train_corpus = [corpus[i] for i in train_indices]
    val_corpus = [corpus[i] for i in val_indices]

    print(f"Разделение корпуса:")
    print(f"  Обучающая выборка: {len(train_corpus)} строк")
    print(f"  Валидационная выборка: {len(val_corpus)} строк")

    return train_corpus, val_corpus


def save_corpus(corpus: List[str], filepath: str) -> None:
    """
    Сохранение корпуса в файл.

    Args:
        corpus: Корпус для сохранения
        filepath: Путь для сохранения
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in corpus:
            f.write(line + '\n')


def main():
    parser = argparse.ArgumentParser(description='Обучение BPE токенизатора')
    parser.add_argument('--input_file', type=str, default='data.txt',
                        help='Путь к файлу с корпусом (по умолчанию: data.txt)')
    parser.add_argument('--num_merges', type=int, default=8000,
                        help='Количество слияний BPE (по умолчанию: 8000)')
    parser.add_argument('--output_dir', type=str, default='./models',
                        help='Директория для сохранения модели (по умолчанию: ./models)')
    parser.add_argument('--val_split', type=float, default=0.1,
                        help='Доля данных для валидации (по умолчанию: 0.1)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Seed для воспроизводимости (по умолчанию: 42)')

    args = parser.parse_args()

    # Устанавливаем seed для воспроизводимости
    np.random.seed(args.seed)

    # Создаем директорию для сохранения, если не существует
    os.makedirs(args.output_dir, exist_ok=True)

    # Читаем корпус
    corpus = read_corpus(args.input_file)

    if len(corpus) == 0:
        print("Ошибка: корпус пуст!")
        return

    # Разделяем на train/val
    train_corpus, val_corpus = split_train_val(corpus, args.val_split)

    # Сохраняем разделенные данные
    save_corpus(train_corpus, os.path.join(args.output_dir, 'train.txt'))
    save_corpus(val_corpus, os.path.join(args.output_dir, 'val.txt'))

    # Создаем и обучаем токенизатор
    print(f"\nСоздание токенизатора с {args.num_merges} слияниями...")
    tokenizer = BPETokenizer(num_merges=args.num_merges)

    # Обучаем на обучающей выборке
    tokenizer.train(train_corpus, verbose=True)

    # Сохраняем токенизатор
    model_path = os.path.join(args.output_dir, f'bpe_model_{args.num_merges}.json')
    tokenizer.save(model_path)

    # Проверяем на валидационной выборке
    print("\nПроверка на валидационной выборке...")

    test_samples = val_corpus[:5]  # Берем первые 5 примеров для проверки

    all_correct = True
    for i, text in enumerate(test_samples):
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        is_correct = (text == decoded)
        all_correct = all_correct and is_correct

        print(f"\nПример {i + 1}:")
        print(f"  Оригинал: {text[:50]}..." if len(text) > 50 else f"  Оригинал: {text}")
        print(f"  Декодированный: {decoded[:50]}..." if len(decoded) > 50 else f"  Декодированный: {decoded}")
        print(f"  Совпадение: {'✓' if is_correct else '✗'}")
        print(f"  Длина токенов: {len(ids)}")

    if all_correct:
        print(f"\n✓ Все проверки пройдены успешно!")
        print(f"  decode(encode(text)) == text для всех тестовых примеров")
    else:
        print(f"\n✗ Некоторые проверки не пройдены")

    # Выводим статистику
    stats = tokenizer.get_stats()
    print(f"\nСтатистика токенизатора:")
    print(f"  Размер словаря: {stats['vocab_size']}")
    print(f"  Количество слияний: {stats['num_merges']}")

    # Вычисляем среднюю длину токенизации на валидации
    print("\nВычисление метрик на валидационной выборке...")
    lengths = []
    for text in val_corpus:
        ids = tokenizer.encode(text)
        lengths.append(len(ids))

    avg_length = np.mean(lengths)
    max_length = np.max(lengths)
    min_length = np.min(lengths)

    # Доля очень длинных токенизаций (top-1%)
    percentile_99 = np.percentile(lengths, 99)
    long_sequences = [l for l in lengths if l > percentile_99]
    long_percent = len(long_sequences) / len(lengths) * 100

    print(f"Метрики на валидации ({len(val_corpus)} примеров):")
    print(f"  Средняя длина: {avg_length:.2f} токенов")
    print(f"  Минимальная длина: {min_length} токенов")
    print(f"  Максимальная длина: {max_length} токенов")
    print(f"  Доля очень длинных (top-1%): {long_percent:.2f}%")

    # Сохраняем метрики
    metrics = {
        'num_merges': args.num_merges,
        'vocab_size': stats['vocab_size'],
        'avg_length': float(avg_length),
        'min_length': int(min_length),
        'max_length': int(max_length),
        'long_percent': float(long_percent),
        'val_size': len(val_corpus)
    }

    import json
    metrics_path = os.path.join(args.output_dir, f'metrics_{args.num_merges}.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"\nМодель сохранена в: {model_path}")
    print(f"Метрики сохранены в: {metrics_path}")


if __name__ == '__main__':
    main()