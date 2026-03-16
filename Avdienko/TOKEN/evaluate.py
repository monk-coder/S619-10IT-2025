import argparse
from bpe_tokenizer import BPETokenizer
from data_utils import read_corpus, calculate_statistics


def main():
    parser = argparse.ArgumentParser(description='Оценка BPE токенизатора')
    parser.add_argument('--tokenizer', type=str, required=True,
                        help='Путь к файлу с обученным токенизатором')
    parser.add_argument('--input', type=str, required=True,
                        help='Путь к файлу с текстом для оценки')
    parser.add_argument('--max-lines', type=int, default=1000,
                        help='Максимальное количество строк для обработки')

    args = parser.parse_args()

    # Загрузка токенизатора
    print(f"Загрузка токенизатора из {args.tokenizer}...")
    tokenizer = BPETokenizer.load(args.tokenizer)
    print(f"Размер словаря: {tokenizer.vocab_size}")

    # Чтение данных
    print(f"Чтение данных из {args.input}...")
    data = read_corpus(args.input, args.max_lines)
    print(f"Загружено {len(data)} строк для оценки")

    # Вычисление статистики
    print("\nВычисление статистики...")
    stats = calculate_statistics(tokenizer, data)

    print("\n=== Статистика токенизации ===")
    print(f"Средняя длина последовательности: {stats['mean_length']:.2f} токенов")
    print(f"Медианная длина: {stats['median_length']:.2f} токенов")
    print(f"Стандартное отклонение: {stats['std_length']:.2f}")
    print(f"Максимальная длина: {stats['max_length']} токенов")
    print(f"Минимальная длина: {stats['min_length']} токенов")
    print(f"95-й перцентиль: {stats['p95_length']:.2f} токенов")
    print(f"99-й перцентиль: {stats['p99_length']:.2f} токенов")
    print(f"Доля очень длинных (>P99): {stats['long_sequences_ratio']:.4f}")
    print(f"Всего токенов: {stats['total_tokens']}")

    # Проверка декодирования
    print("\n=== Проверка декодирования ===")
    test_passed = 0
    test_total = min(100, len(data))

    for i in range(test_total):
        text = data[i]
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        if text == decoded:
            test_passed += 1
        else:
            if test_passed == test_total - 1:  # Показать только первую ошибку
                print(f"\nОшибка в строке {i}:")
                print(f"Оригинал: {text[:100]}...")
                print(f"Декодировано: {decoded[:100]}...")

    print(f"\nПроверка decode(encode(text)) == text:")
    print(f"Пройдено: {test_passed}/{test_total} ({test_passed / test_total * 100:.1f}%)")

    # Примеры токенизации
    print("\n=== Примеры токенизации ===")
    sample_texts = data[:3]
    for i, text in enumerate(sample_texts):
        tokens = tokenizer.tokenize(text)
        ids = tokenizer.encode(text)
        print(f"\nПример {i + 1}:")
        print(f"Текст: {text[:50]}..." if len(text) > 50 else f"Текст: {text}")
        print(f"Токены: {tokens[:10]}..." if len(tokens) > 10 else f"Токены: {tokens}")
        print(f"ID: {ids[:10]}..." if len(ids) > 10 else f"ID: {ids}")


if __name__ == '__main__':
    main()