import argparse
import os
from bpe_tokenizer import BPETokenizer
from data_utils import read_corpus, split_train_val


def main():
    parser = argparse.ArgumentParser(description='Обучение BPE токенизатора')
    parser.add_argument('--input', type=str, required=True,
                        help='Путь к входному файлу с текстом')
    parser.add_argument('--output', type=str, default='tokenizer.pkl',
                        help='Путь для сохранения обученного токенизатора')
    parser.add_argument('--merges-json', type=str, default='bpe_merges.json',
                        help='Путь для сохранения правил слияний в JSON')
    parser.add_argument('--num-merges', type=int, default=8000,
                        help='Количество операций слияния BPE')
    parser.add_argument('--val-size', type=float, default=0.1,
                        help='Доля данных для валидации')
    parser.add_argument('--max-lines', type=int, default=None,
                        help='Максимальное количество строк для обработки')
    parser.add_argument('--seed', type=int, default=42,
                        help='Seed для воспроизводимости')

    args = parser.parse_args()

    # Чтение корпуса
    print(f"Чтение корпуса из {args.input}...")
    corpus = read_corpus(args.input, args.max_lines)
    print(f"Загружено {len(corpus)} строк")

    # Разделение на train/val
    print(f"Разделение данных (train/val={1 - args.val_size}/{args.val_size})...")
    train_data, val_data = split_train_val(corpus, args.val_size, args.seed)
    print(f"Train: {len(train_data)} строк, Val: {len(val_data)} строк")

    # Обучение токенизатора
    print(f"Обучение BPE токенизатора с {args.num_merges} слияниями...")
    tokenizer = BPETokenizer.train(
        corpus=train_data,
        num_merges=args.num_merges,
        special_tokens=['<unk>', '<pad>', '<s>', '</s>'],
        verbose=True
    )

    print(f"Размер словаря: {tokenizer.vocab_size}")

    # Тестирование на валидационных данных
    print("\nТестирование на валидационных данных...")
    test_text = val_data[0][:100] + "..." if len(val_data[0]) > 100 else val_data[0]
    print(f"Пример текста: {test_text}")

    ids = tokenizer.encode(test_text)
    decoded = tokenizer.decode(ids)

    print(f"Закодировано: {len(ids)} токенов")
    print(f"Декодировано: {decoded}")
    print(f"Совпадение: {test_text == decoded}")

    # Сохранение токенизатора
    print(f"\nСохранение токенизатора в {args.output}...")
    tokenizer.save(args.output)

    # Сохранение правил слияний
    print(f"Сохранение правил слияний в {args.merges_json}...")
    tokenizer.save_merges_json(args.merges_json)

    print("Обучение завершено!")


if __name__ == '__main__':
    main()