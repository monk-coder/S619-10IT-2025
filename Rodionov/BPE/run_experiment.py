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
    """Создание качественного тестового корпуса для BPE."""

    texts = [
        """Byte Pair Encoding (BPE) is a simple and effective data compression algorithm that works by iteratively replacing the most frequent pair of bytes with a single new byte. In NLP, BPE is used for subword tokenization to handle out-of-vocabulary words by breaking them into known subword units. The algorithm builds a vocabulary of subwords by merging characters based on their frequency in the training corpus.""",

        """Modern language models like GPT-3, GPT-4, BERT, RoBERTa, and T5 all use subword tokenization. GPT models use BPE, BERT uses WordPiece, and SentencePiece is used in many multilingual models. These tokenizers typically have vocabulary sizes between 30,000 and 50,000 tokens, which balances between coverage and efficiency.""",

        """Subword tokenization solves the problem of open vocabularies in NLP. Instead of having a fixed word vocabulary that can't handle rare or new words, subword models can represent any text by combining smaller units. This is especially important for morphologically rich languages where words can have many different forms.""",

        """Byte Pair Encoding особенно эффективен для русского языка из-за его богатой морфологии. Например, слово "программирование" имеет множество форм: программирования, программированию, программированием, программировании, программист, программиста, программисту, программистом, программисты, программистов, программистам и так далее.""",

        """Современные нейросетевые модели обрабатывают естественный язык с помощью трансформеров. Механизм самовнимания позволяет моделям учитывать контекст при обработке каждого слова. Многослойные архитектуры с миллиардами параметров обучаются на огромных корпусах текстов из интернета, книг и научных статей.""",

        """Искусственный интеллект развивается невероятными темпами. Каждый год появляются новые архитектуры нейронных сетей, улучшающие качество обработки текстов, изображений и звука. Модели становятся больше, данные - объемнее, а задачи - сложнее и интереснее.""",

        """Трансформеры - это архитектура нейронных сетей, основанная на механизме внимания. В отличие от рекуррентных сетей, трансформеры могут обрабатывать все слова последовательности параллельно, что значительно ускоряет обучение. Модели BERT и GPT стали прорывом в понимании и генерации текста.""",

        """Токенизация - это первый и критически важный этап обработки текста. От качества токенизации зависит, насколько хорошо модель сможет понимать язык. Плохая токенизация может привести к потере информации и ухудшению качества работы всей модели.""",

        """Привет мир!""",
        """Как дела?""",
        """Сегодня отличная погода для прогулки по парку.""",
        """Я люблю программировать на Python и изучать машинное обучение.""",
        """Очень длинное предложение, которое содержит множество слов и должно породить много токенов при кодировании, чтобы проверить работу алгоритма на длинных последовательностях текста.""",

        """токенизация токенизации токенизацией токенизацию""",
        """обучение обучения обучению обучением обучении""",
        """модель модели моделью модели моделей моделям""",
        """алгоритм алгоритма алгоритму алгоритмом алгоритме алгоритмы""",

        """антидисестаблишментарианизм""",
        """электрокардиография""",
        """параллелепипед""",
        """достопримечательность""",
        """высококвалифицированный""",
        """сельскохозяйственный""",
        """межправительственный""",
        """экспериментирование""",

        """12345 67890 3.14159 42 1000000""",
        """!@#$%^&*()_+-=[]{}|;:'",.<>/?~`""",
        """email@example.com https://github.com +7 (999) 123-45-67""",

        """Hello world! Bonjour le monde! Hola mundo! Ciao mondo!""",
        """Привет мир! 你好世界! Hallo Welt! 안녕하세요 세계!""",

        """ing ing ing ing running walking talking playing""",
        """ed ed ed ed worked played walked talked""",
        """pre pre pre pre prefix predict prepare preview""",
        """un un un un unhappy unknown unclear unable""",

        """tokenization subword bytepair encoding vocabulary merge frequency pair algorithm""",
        """neural network transformer attention layer embedding vector dimension""",
        """gradient descent backpropagation optimization loss function parameter""",

        """Donaudampfschifffahrtsgesellschaftskapitän""",
        """Kindercarnavalsoptochtvoorbereidingswerkzaamheden""",
        """Pneumonoultramicroscopicsilicovolcanoconiosis""",

        """Привет! Как жизнь? Чем занимаешься? Давно не виделись!""",
        """Ну, это самое, понимаешь, такое дело... Короче, я это, того.""",
        """Окей, гугл, как пройти в библиотеку? Siri, включи музыку!""",

        """BPE - это жадный алгоритм, который на каждом шаге находит самую частую пару соседних символов или подслов и заменяет их новым символом. Процесс продолжается до достижения желаемого размера словаря.""",

        """WordPiece похож на BPE, но использует вероятностную модель для выбора слияний. Unigram токенизация, наоборот, начинает с большого словаря и постепенно удаляет наименее полезные токены.""",

        """Обработка естественного языка. Компьютерная лингвистика. Машинный перевод. Распознавание речи. Генерация текста. Анализ тональности. Извлечение информации. Ответы на вопросы. Суммаризация. Диалоговые системы.""",

        """Здравствуйте! Как ваши дела? Надеюсь, всё хорошо... А у меня - просто отлично! Хотя, если честно, есть некоторые проблемы: мало времени, много работы, но я справлюсь!""",
    ]

    full_text = "\n".join(texts)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_text)

    return [line.strip() for line in full_text.split('\n') if line.strip()]


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