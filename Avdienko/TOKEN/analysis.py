import argparse
import matplotlib.pyplot as plt
from bpe_tokenizer import BPETokenizer
from data_utils import read_corpus, split_train_val, calculate_statistics


def main():
    parser = argparse.ArgumentParser(description='Анализ BPE с разным количеством слияний')
    parser.add_argument('--input', type=str, required=True,
                        help='Путь к входному файлу с текстом')
    parser.add_argument('--merges', type=int, nargs='+', default=[0, 2000, 8000],
                        help='Количество слияний для сравнения')
    parser.add_argument('--val-size', type=float, default=0.1,
                        help='Доля данных для валидации')
    parser.add_argument('--max-lines', type=int, default=5000,
                        help='Максимальное количество строк для обработки')
    parser.add_argument('--seed', type=int, default=42,
                        help='Seed для воспроизводимости')
    parser.add_argument('--output', type=str, default='bpe_analysis.png',
                        help='Путь для сохранения графика')

    args = parser.parse_args()

    # Чтение корпуса
    print(f"Чтение корпуса из {args.input}...")
    corpus = read_corpus(args.input, args.max_lines)
    print(f"Загружено {len(corpus)} строк")

    # Разделение на train/val
    train_data, val_data = split_train_val(corpus, args.val_size, args.seed)

    results = []

    # Обучение и оценка для каждого значения num_merges
    for num_merges in args.merges:
        print(f"\n=== Обучение с num_merges={num_merges} ===")

        # Обучение токенизатора
        tokenizer = BPETokenizer.train(
            corpus=train_data,
            num_merges=num_merges,
            special_tokens=['<unk>', '<pad>', '<s>', '</s>'],
            verbose=False
        )

        # Вычисление статистики
        stats = calculate_statistics(tokenizer, val_data)

        results.append({
            'num_merges': num_merges,
            'vocab_size': tokenizer.vocab_size,
            'mean_length': stats['mean_length'],
            'p95_length': stats['p95_length'],
            'p99_length': stats['p99_length'],
            'long_sequences_ratio': stats['long_sequences_ratio']
        })

        print(f"Размер словаря: {tokenizer.vocab_size}")
        print(f"Средняя длина: {stats['mean_length']:.2f}")
        print(f"Доля длинных последовательностей: {stats['long_sequences_ratio']:.4f}")

    # Вывод результатов в таблицу
    print("\n=== Сводная таблица результатов ===")
    print(f"{'Num Merges':>12} {'Vocab Size':>12} {'Mean Length':>12} {'P95 Length':>12} {'Long Ratio':>12}")
    print("-" * 60)
    for r in results:
        print(f"{r['num_merges']:>12} {r['vocab_size']:>12} {r['mean_length']:>12.2f} "
              f"{r['p95_length']:>12.2f} {r['long_sequences_ratio']:>12.4f}")

    # Построение графиков
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # График 1: Средняя длина vs Количество слияний
    axes[0, 0].plot([r['num_merges'] for r in results],
                    [r['mean_length'] for r in results],
                    'bo-', linewidth=2)
    axes[0, 0].set_xlabel('Количество слияний')
    axes[0, 0].set_ylabel('Средняя длина последовательности')
    axes[0, 0].set_title('Зависимость средней длины от количества слияний')
    axes[0, 0].grid(True, alpha=0.3)

    # График 2: Размер словаря vs Количество слияний
    axes[0, 1].plot([r['num_merges'] for r in results],
                    [r['vocab_size'] for r in results],
                    'ro-', linewidth=2)
    axes[0, 1].set_xlabel('Количество слияний')
    axes[0, 1].set_ylabel('Размер словаря')
    axes[0, 1].set_title('Рост словаря с увеличением слияний')
    axes[0, 1].grid(True, alpha=0.3)

    # График 3: Процентили длин
    x = [r['num_merges'] for r in results]
    axes[1, 0].plot(x, [r['p95_length'] for r in results], 'g^-', label='P95', linewidth=2)
    axes[1, 0].plot(x, [r['p99_length'] for r in results], 'ms-', label='P99', linewidth=2)
    axes[1, 0].set_xlabel('Количество слияний')
    axes[1, 0].set_ylabel('Длина последовательности')
    axes[1, 0].set_title('Процентили длин последовательностей')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # График 4: Доля длинных последовательностей
    axes[1, 1].plot(x, [r['long_sequences_ratio'] for r in results],
                    'co-', linewidth=2)
    axes[1, 1].set_xlabel('Количество слияний')
    axes[1, 1].set_ylabel('Доля последовательностей > P99')
    axes[1, 1].set_title('Доля очень длинных последовательностей')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"\nГрафики сохранены в {args.output}")

    # Сохранение результатов в файл
    import json
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Результаты анализа сохранены в analysis_results.json")


if __name__ == '__main__':
    main()