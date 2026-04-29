import os
import random
import matplotlib.pyplot as plt
import numpy as np
from bpe_tokenizer import BPETokenizer


def load_data(filepath):
    """Загрузка данных из файла."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Очистка от пустых строк и лишних пробелов по краям
    lines = [line.strip() for line in lines if line.strip()]
    return lines


def split_data(lines, test_ratio=0.1):
    """Разбиение данных на обучающую и валидационную выборки."""
    random.seed(42)  # Фиксируем seed для воспроизводимости
    random.shuffle(lines)
    split_idx = int(len(lines) * (1 - test_ratio))
    train_data = lines[:split_idx]
    val_data = lines[split_idx:]
    return train_data, val_data


def evaluate_tokenizer(tokenizer, val_data):
    """
    Проверка обратимости (decode(encode(x)) == x) и сбор метрик.
    """
    total_len = 0
    lengths = []
    errors = 0

    # Для демонстрации можно проверить первые 1000 строк, чтобы не ждать долго,
    # но для строгой проверки лучше пройти по всем.
    for text in val_data:
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)

        # Строгая проверка равенства
        if decoded != text:
            errors += 1
            # Можно раскомментировать для отладки конкретных ошибок:
            # print(f"Error: Original: '{text}' | Decoded: '{decoded}'")

        total_len += len(encoded)
        lengths.append(len(encoded))

    avg_len = total_len / len(val_data) if val_data else 0

    # Доля очень длинных токенизаций (top 1%)
    long_ratio = 0
    if lengths:
        threshold = np.percentile(lengths, 99)
        long_count = sum(1 for l in lengths if l > threshold)
        long_ratio = long_count / len(lengths)

    return {
        "avg_length": avg_len,
        "vocab_size": len(tokenizer.vocab),
        "errors": errors,
        "long_tokenization_ratio": long_ratio
    }


def experiment_with_merges(train_data, val_data, merge_counts=[0, 100, 500, 1000]):
    """Эксперимент с разным количеством слияний (merges)."""
    results = []

    for num_merges in merge_counts:
        print(f"\n--- Experiment: num_merges={num_merges} ---")
        tokenizer = BPETokenizer()
        # Обучаем новый экземпляр токенизатора для каждого эксперимента
        tokenizer.train(train_data, num_merges=num_merges)

        metrics = evaluate_tokenizer(tokenizer, val_data)
        metrics['num_merges'] = num_merges
        results.append(metrics)

        print(f"Vocab Size: {metrics['vocab_size']}")
        print(f"Avg Length: {metrics['avg_length']:.2f}")
        print(f"Errors (decode!=encode): {metrics['errors']}")

    return results


def plot_results(results):
    """Построение графиков зависимости метрик от количества слияний."""
    merges = [r['num_merges'] for r in results]
    avg_lengths = [r['avg_length'] for r in results]
    vocab_sizes = [r['vocab_size'] for r in results]

    plt.figure(figsize=(12, 5))

    # График 1: Средняя длина последовательности
    plt.subplot(1, 2, 1)
    plt.plot(merges, avg_lengths, marker='o', color='b')
    plt.title('Average Token Length vs Num Merges')
    plt.xlabel('Num Merges')
    plt.ylabel('Avg Tokens per Sentence')
    plt.grid(True)

    # График 2: Размер словаря
    plt.subplot(1, 2, 2)
    plt.plot(merges, vocab_sizes, marker='s', color='orange')
    plt.title('Vocabulary Size vs Num Merges')
    plt.xlabel('Num Merges')
    plt.ylabel('Vocab Size')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('bpe_metrics.png')
    plt.show()
    print("График сохранен как bpe_metrics.png")


def main():
    # Путь к файлу данных согласно заданию (папка '0')
    data_path = os.path.join('0', 'data.txt')

    print(f"Поиск данных по пути: {data_path}")

    if not os.path.exists(data_path):
        print(f"Ошибка: Файл '{data_path}' не найден.")
        print("Убедитесь, что вы запустили скрипт из корневой папки проекта,")
        print("и что папка '0' с файлом 'data.txt' находится рядом с main.py.")
        return

    print("Загрузка данных...")
    try:
        lines = load_data(data_path)
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    if len(lines) < 10:
        print("Предупреждение: Слишком мало данных для качественного обучения.")

    train_data, val_data = split_data(lines)

    print(f"Размер обучающей выборки: {len(train_data)} строк")
    print(f"Размер валидационной выборки: {len(val_data)} строк")

    # 1. Обучение финальной модели (например, 1000 слияний)
    final_merges = 1000
    print(f"\nОбучение финального токенизатора ({final_merges} merges)...")
    tokenizer = BPETokenizer()
    tokenizer.train(train_data, num_merges=final_merges)

    # Сохранение модели
    tokenizer.save("bpe_model.json")

    # Загрузка модели для проверки (тестируем save/load)
    print("\nПроверка загрузки модели...")
    tokenizer_loaded = BPETokenizer()
    tokenizer_loaded.load("bpe_model.json")

    # Проверка обратимости на валидации
    print("\nПроверка условия decode(encode(x)) == x на валидационной выборке...")
    metrics = evaluate_tokenizer(tokenizer_loaded, val_data)

    print(f"\n--- Итоговые метрики ---")
    print(f"Размер словаря: {metrics['vocab_size']}")
    print(f"Средняя длина последовательности: {metrics['avg_length']:.2f}")
    print(f"Количество ошибок декодирования: {metrics['errors']}")

    if metrics['errors'] > 0:
        print("ВНИМАНИЕ: Есть ошибки декодирования! Проверьте реализацию.")
    else:
        print("УСПЕХ: Условие обратимости выполнено для всех примеров.")

    # 2. Эксперимент с разным количеством слияний
    print("\nЗапуск экспериментов с разным числом слияний...")
    # Можно настроить список мерджей под себя
    exp_results = experiment_with_merges(train_data, val_data, merge_counts=[0, 200, 500, 1000])

    plot_results(exp_results)


if __name__ == "__main__":
    main()
