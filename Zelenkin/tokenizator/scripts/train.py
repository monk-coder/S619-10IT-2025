#!/usr/bin/env python
"""Скрипт для обучения BPE токенизатора."""

import argparse
import sys
from pathlib import Path

# Добавляем путь к src (если его нет)
sys.path.append(str(Path(__file__).parent.parent))

from src.tokenizer import BPETokenizer, TokenizerConfig
from src.utils.data_loader import DataLoader
from src.utils.metrics import TokenizerMetrics
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description='Обучение BPE токенизатора')
    parser.add_argument('--data', type=str, default='data/raw/data.txt',
                        help='Путь к файлу с данными')
    parser.add_argument('--merges', type=int, nargs='+', default=[2000, 8000],
                        help='Количество слияний для обучения')
    parser.add_argument('--output-dir', type=str, default='models',
                        help='Директория для сохранения моделей')
    parser.add_argument('--val-size', type=float, default=0.1,
                        help='Размер валидационной выборки')
    parser.add_argument('--lowercase', action='store_true', default=True,
                        help='Приводить к нижнему регистру')
    return parser.parse_args()


def main():
    args = parse_args()

    # Создаем директории
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Загрузка данных
    print("=" * 60)
    print("ЗАГРУЗКА ДАННЫХ")
    print("=" * 60)

    loader = DataLoader(args.data)
    corpus = loader.load_corpus()
    print(f"Загружено {len(corpus)} строк")

    # Разбиение на train/val
    train_data, val_data = loader.train_val_split(corpus, val_size=args.val_size)
    print(f"Train: {len(train_data)} строк")
    print(f"Val: {len(val_data)} строк")

    # Обучение для каждого количества слияний
    results = {}

    for num_merges in args.merges:
        print("\n" + "=" * 60)
        print(f"ОБУЧЕНИЕ С {num_merges} СЛИЯНИЯМИ")
        print("=" * 60)

        # Конфигурация
        config = TokenizerConfig(
            num_merges=num_merges,
            lowercase=args.lowercase
        )

        # Обучение
        tokenizer = BPETokenizer(config)
        tokenizer.train(train_data)

        # Сохранение
        save_path = output_dir / f"bpe_tokenizer_{num_merges}.json"
        tokenizer.save(save_path)
        print(f"Модель сохранена в {save_path}")

        # Статистика
        metrics = TokenizerMetrics(tokenizer)
        stats = metrics.get_statistics(val_data)

        print("\nСтатистика на валидации:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        results[num_merges] = {
            'tokenizer': tokenizer,
            'stats': stats
        }

        # Проверка обратимости
        print("\nПроверка обратимости:")
        test_texts = val_data[:5]
        all_correct = True

        for i, text in enumerate(test_texts):
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)

            expected = text.lower() if args.lowercase else text
            is_correct = decoded == expected

            if not is_correct:
                all_correct = False
                print(f"  {i + 1}: ✗ '{text[:50]}...'")
                print(f"     Expected: '{expected[:50]}...'")
                print(f"     Got: '{decoded[:50]}...'")
            else:
                print(f"  {i + 1}: ✓ '{text[:50]}...' ({len(encoded)} токенов)")

        if all_correct:
            print("  Все проверки пройдены успешно!")

    print("\n" + "=" * 60)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == "__main__":
    main()