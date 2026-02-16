#!/usr/bin/env python3
"""
Главный скрипт для запуска всего эксперимента BPE одной командой.
Запуск: python run_experiment.py
"""

import os
import json
import numpy as np
from typing import List, Tuple
import matplotlib.pyplot as plt
from bpe_tokenizer import BPETokenizer


def create_sample_corpus(filepath: str = "data/sample_corpus.txt"):
    """
    Создание тестового корпуса, если его нет.
    """
    print("Создание тестового корпуса...")
    sample_text = """Машинное обучение — это область искусственного интеллекта, которая изучает алгоритмы, способные обучаться на данных.
BPE (Byte Pair Encoding) — это алгоритм субсловной токенизации, который разбивает слова на более мелкие части.
Нейронные сети, трансформеры, внимание — все эти концепции являются фундаментальными для современных NLP систем.
Токенизация является первым шагом в обработке естественного языка.
Частотный анализ и статистические методы лежат в основе BPE алгоритма.
Глубокое обучение революционизировало компьютерное зрение и NLP.
BERT, GPT, T5 — это современные языковые модели, использующие BPE.
Субсловная токенизация помогает работать с огромными словарями.
Качество токенизации влияет на производительность моделей.
Привет, мир! Как дела? Это тестовый текст для проверки работы BPE токенизатора.
Русский язык обладает богатой морфологией, что делает BPE особенно полезным.
Английский текст тоже можно токенизировать с помощью этого метода.
12345 67890 — это числа, которые тоже нужно уметь обрабатывать.
Специальные символы: !@#$%^&*()_+{}[]|\\:";'<>?,./~
Большие и маленькие буквы: ABCD abcd.
Повторяющиеся слова: текст текст текст для анализа частот.
Разные языки: hello world, bonjour le monde, привет мир.
Длинные слова: антидисестаблишментарианизм и электрогазосварщик.
Короткие слова: я, ты, он, она, оно, мы, вы, они.
Предложения разной длины. Очень короткие. А это уже более длинное предложение для тестирования работы алгоритма на текстах разного размера и сложности.
"""

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(sample_text)

    print(f"Тестовый корпус создан: {filepath}")

    return [line.strip() for line in sample_text.split('\n') if line.strip()]


def load_data(filepath: str) -> List[str]:
    """
    Загрузка данных из файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            print(f"Файл {filepath} пустой. Создаю тестовый корпус...")
            return create_sample_corpus(filepath)

        lines = [line.strip() for line in content.split('\n') if line.strip()]

        print(f"Загружено {len(lines)} строк из {filepath}")
        print(f"Общий объем текста: {len(content)} символов")

        print("Первые 3 строки:")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line[:80]}...")

        return lines
    except FileNotFoundError:
        print(f"Файл {filepath} не найден. Создаю тестовый корпус...")
        return create_sample_corpus(filepath)


def split_data(data: List[str], train_ratio: float = 0.8) -> Tuple[List[str], List[str]]:
    """
    Разделение данных на train и validation.
    """
    if not data:
        print("Ошибка: данные пустые!")
        data = ["Тестовый текст для BPE.", "Еще один пример текста."]

    np.random.seed(42)
    indices = np.random.permutation(len(data))
    split_idx = int(train_ratio * len(data))

    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]

    train_data = [data[i] for i in train_indices]
    val_data = [data[i] for i in val_indices]

    print(f"Train: {len(train_data)} строк")
    print(f"Validation: {len(val_data)} строк")

    return train_data, val_data


def train_and_evaluate(num_merges: int, train_data: List[str], val_data: List[str],
                       model_name: str = None) -> dict:
    """
    Обучение и оценка токенизатора с заданным num_merges.
    """
    if model_name is None:
        model_name = f"bpe_{num_merges}"

    print(f"\n{'=' * 60}")
    print(f"Эксперимент с num_merges = {num_merges}")
    print(f"{'=' * 60}")

    tokenizer = BPETokenizer()
    tokenizer.train(train_data, num_merges=num_merges, verbose=True)

    model_path = f"models/{model_name}.json"
    tokenizer.save(model_path)

    print("\nТестирование корректности decode(encode(text)) == text:")

    if not val_data:
        print("  Нет валидационных данных для тестирования")
        test_samples = train_data[:3] if train_data else ["Тестовый текст"]
    else:
        test_samples = val_data[:3]

    all_correct = True

    for i, text in enumerate(test_samples):
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)

        original_norm = ' '.join(text.split())
        decoded_norm = ' '.join(decoded.split())

        if original_norm == decoded_norm:
            print(f"  ✓ Пример {i + 1}: текст восстановлен корректно")
            print(f"    Текст: '{text[:50]}...'")
            print(f"    Токенов: {len(encoded)}")
        else:
            print(f"  ✗ Пример {i + 1}: текст не восстановлен полностью")
            print(f"    Оригинал: '{text[:50]}...'")
            print(f"    Восстановленный: '{decoded[:50]}...'")
            all_correct = False

    if all_correct:
        print("  Все тесты пройдены успешно!")
    else:
        print("  Некоторые тесты не пройдены!")

    stats_data = val_data if val_data else train_data
    if not stats_data:
        stats_data = ["Минимальный текст для статистики"]

    stats = tokenizer.get_stats(stats_data)
    stats['num_merges'] = num_merges
    stats['model_name'] = model_name

    stats_path = f"results/stats_{model_name}.json"
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\nСтатистика сохранена в {stats_path}")
    print("\nСтатистика:")
    for key, value in stats.items():
        if key not in ['model_name', 'total_tokens', 'num_samples']:
            print(f"  {key}: {value}")

    return stats


def compare_experiments(merge_values: List[int], results_dir: str = "results"):
    """
    Сравнение разных значений num_merges и создание графиков.
    """
    print(f"\n{'=' * 60}")
    print("Сравнение разных значений num_merges")
    print(f"{'=' * 60}")
    all_stats = []
    for num_merges in merge_values:
        stats_path = f"{results_dir}/stats_bpe_{num_merges}.json"
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                all_stats.append(stats)
                print(f"Загружена статистика для num_merges={num_merges}")
        except FileNotFoundError:
            print(f"Файл {stats_path} не найден, пропускаем...")

    if not all_stats:
        print("Нет данных для сравнения")
        return

    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        ax = axes[0, 0]
        merges = [s['num_merges'] for s in all_stats]
        avg_lengths = [s['avg_length'] for s in all_stats]
        ax.plot(merges, avg_lengths, 'o-', linewidth=2, markersize=8)
        ax.set_xlabel('Количество слияний (num_merges)', fontsize=12)
        ax.set_ylabel('Средняя длина (токены)', fontsize=12)
        ax.set_title('Зависимость средней длины от количества слияний', fontsize=14)
        ax.grid(True, alpha=0.3)

        for i, (x, y) in enumerate(zip(merges, avg_lengths)):
            ax.text(x, y, f'{y:.1f}', ha='center', va='bottom', fontsize=10)

        ax = axes[0, 1]
        vocab_sizes = [s['vocab_size'] for s in all_stats]
        ax.plot(merges, vocab_sizes, 's-', linewidth=2, markersize=8, color='orange')
        ax.set_xlabel('Количество слияний (num_merges)', fontsize=12)
        ax.set_ylabel('Размер словаря', fontsize=12)
        ax.set_title('Зависимость размера словаря от количества слияний', fontsize=14)
        ax.grid(True, alpha=0.3)

        for i, (x, y) in enumerate(zip(merges, vocab_sizes)):
            ax.text(x, y, f'{y}', ha='center', va='bottom', fontsize=10)

        ax = axes[1, 0]
        p99_lengths = [s['p99_length'] for s in all_stats]
        ax.plot(merges, p99_lengths, '^-', linewidth=2, markersize=8, color='green')
        ax.set_xlabel('Количество слияний (num_merges)', fontsize=12)
        ax.set_ylabel('99-й процентиль длины', fontsize=12)
        ax.set_title('Зависимость 99-го процентиля от количества слияний', fontsize=14)
        ax.grid(True, alpha=0.3)

        for i, (x, y) in enumerate(zip(merges, p99_lengths)):
            ax.text(x, y, f'{y:.1f}', ha='center', va='bottom', fontsize=10)

        ax = axes[1, 1]
        long_ratios = [s['long_ratio'] * 100 for s in all_stats]  # В процентах
        ax.bar(range(len(merges)), long_ratios, color=['blue', 'orange', 'green', 'red'])
        ax.set_xlabel('Количество слияний', fontsize=12)
        ax.set_ylabel('Доля очень длинных (%)', fontsize=12)
        ax.set_title('Доля последовательностей длиннее 99-го процентиля', fontsize=14)
        ax.set_xticks(range(len(merges)))
        ax.set_xticklabels([str(m) for m in merges])
        ax.grid(True, alpha=0.3, axis='y')

        for i, v in enumerate(long_ratios):
            ax.text(i, v, f'{v:.1f}%', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()

        plots_dir = "plots"
        os.makedirs(plots_dir, exist_ok=True)
        plot_path = f"{plots_dir}/bpe_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"\nГрафики сохранены в {plot_path}")

        print("\n" + "=" * 80)
        print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
        print("=" * 80)
        print(f"{'num_merges':<12} {'vocab_size':<12} {'avg_length':<12} "
              f"{'p99_length':<12} {'long_ratio (%)':<15}")
        print("-" * 80)

        for stats in all_stats:
            print(f"{stats['num_merges']:<12} {stats['vocab_size']:<12} "
                  f"{stats['avg_length']:<12.2f} {stats['p99_length']:<12.2f} "
                  f"{stats['long_ratio'] * 100:<15.2f}")

        print("=" * 80)

        plt.show()

    except Exception as e:
        print(f"Ошибка при создании графиков: {e}")
        print("Продолжаем без графиков...")


def run_interactive_demo():
    """
    Интерактивная демонстрация работы токенизатора.
    """
    print(f"\n{'=' * 60}")
    print("ИНТЕРАКТИВНАЯ ДЕМОНСТРАЦИЯ")
    print(f"{'=' * 60}")

    if not os.path.exists("models"):
        print("Папка models не найдена. Сначала запустите обучение.")
        return

    models = [f for f in os.listdir("models") if f.endswith('.json')]
    if not models:
        print("Нет обученных моделей. Сначала запустите обучение.")
        return

    latest_model = sorted(models)[-1]
    model_path = f"models/{latest_model}"

    print(f"Загрузка модели: {latest_model}")

    try:
        tokenizer = BPETokenizer()
        tokenizer.load(model_path)

        print(f"Модель загружена. Размер словаря: {tokenizer.vocab_size}")
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        return

    print("\nПримеры работы токенизатора:")
    print("(Введите 'quit' для выхода или 'test' для тестовых примеров)")

    test_examples = [
        "Привет, мир!",
        "BPE токенизация работает отлично.",
        "Нейронные сети обучаются на данных.",
        "Субсловная сегментация помогает с редкими словами."
    ]

    while True:
        print("\n" + "-" * 40)

        try:
            user_input = input("Введите текст для токенизации: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из демо...")
            break

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'test':
            for example in test_examples:
                print(f"\nПример: '{example}'")
                encoded = tokenizer.encode(example)
                decoded = tokenizer.decode(encoded)
                print(f"  ID токенов: {encoded}")
                print(f"  Количество токенов: {len(encoded)}")

                tokens = [tokenizer.vocab.get(id, '<unk>') for id in encoded[:10]]
                print(f"  Токены (первые 10): {tokens}")
                if len(encoded) > 10:
                    print(f"  ... и еще {len(encoded) - 10} токенов")

                print(f"  Декодированный текст: '{decoded}'")

                original_norm = ' '.join(example.split())
                decoded_norm = ' '.join(decoded.split())
                print(f"  Совпадение: {'✓' if original_norm == decoded_norm else '✗'}")
            continue
        elif not user_input:
            continue

        try:
            encoded = tokenizer.encode(user_input)
            decoded = tokenizer.decode(encoded)

            print(f"\nРезультат:")
            print(f"  Оригинальный текст: '{user_input}'")
            print(f"  Количество токенов: {len(encoded)}")
            print(f"  ID токенов: {encoded}")

            tokens = [tokenizer.vocab.get(id, '<unk>') for id in encoded]
            if len(tokens) <= 20:
                print(f"  Токены: {tokens}")
            else:
                print(f"  Токены (первые 20): {tokens[:20]}")
                print(f"  ... и еще {len(tokens) - 20} токенов")

            print(f"  Декодированный текст: '{decoded}'")

            original_norm = ' '.join(user_input.split())
            decoded_norm = ' '.join(decoded.split())

            if original_norm == decoded_norm:
                print("  ✓ decode(encode(text)) == text")
            else:
                print("  ✗ decode(encode(text)) != text")
                print(f"  Оригинал (норм): '{original_norm}'")
                print(f"  Декодированный (норм): '{decoded_norm}'")

        except Exception as e:
            print(f"  Ошибка при обработке текста: {e}")


def main():
    """
    Главная функция, запускающая весь эксперимент.
    """
    print("=" * 70)
    print("BPE TOKENIZER EXPERIMENT - ПОЛНЫЙ ЭКСПЕРИМЕНТ")
    print("=" * 70)

    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    DATA_FILE = "data/sample_corpus.txt"
    MERGE_VALUES = [0, 500, 2000]

    print("\n1. ЗАГРУЗКА ДАННЫХ")
    print("-" * 40)
    data = load_data(DATA_FILE)

    if not data:
        print("ОШИБКА: Не удалось загрузить или создать данные!")
        print("Создаю минимальный набор данных...")
        data = [
            "Машинное обучение — это область искусственного интеллекта.",
            "BPE (Byte Pair Encoding) — алгоритм субсловной токенизации.",
            "Нейронные сети обучаются на данных.",
            "Токенизация — первый шаг в обработке естественного языка.",
            "Привет, мир! Это тестовый текст."
        ]

    print("\n2. РАЗДЕЛЕНИЕ ДАННЫХ")
    print("-" * 40)
    train_data, val_data = split_data(data, train_ratio=0.8)

    print("\n3. ОБУЧЕНИЕ МОДЕЛЕЙ")
    print("-" * 40)

    all_stats = []
    for num_merges in MERGE_VALUES:
        try:
            stats = train_and_evaluate(num_merges, train_data, val_data)
            all_stats.append(stats)
        except Exception as e:
            print(f"Ошибка при обучении с num_merges={num_merges}: {e}")
            print("Продолжаем со следующим значением...")

    print("\n4. АНАЛИЗ И СРАВНЕНИЕ")
    print("-" * 40)
    compare_experiments(MERGE_VALUES)

    print("\n5. ДЕМОНСТРАЦИЯ РАБОТЫ")
    print("-" * 40)
    run_interactive_demo()

    print("\n" + "=" * 70)
    print("ЭКСПЕРИМЕНТ ЗАВЕРШЕН!")
    print("=" * 70)
    print("\nСозданные файлы:")

    for dir_name in ["data", "models", "results", "plots"]:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            if files:
                print(f"  {dir_name}/: {len(files)} файлов")
            else:
                print(f"  {dir_name}/: папка пуста")

    print("\nДля повторного запуска демо используйте: python run_experiment.py")
    print("Или загрузите модель и протестируйте:")
    print("  from bpe_tokenizer import BPETokenizer")
    print("  tokenizer = BPETokenizer()")
    print("  tokenizer.load('models/bpe_2000.json')")
    print("  encoded = tokenizer.encode('Ваш текст')")


if __name__ == "__main__":
    main()