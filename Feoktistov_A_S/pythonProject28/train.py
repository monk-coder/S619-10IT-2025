import argparse
import os
import sys
import json
from typing import List, Tuple, Dict
import numpy as np

# Добавляем путь к текущей директории для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenizer import BPETokenizer


def parse_arguments() -> argparse.Namespace:
    """
    Парсинг аргументов командной строки.

    Returns:
        argparse.Namespace: Распарсенные аргументы
    """
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

    return parser.parse_args()


def setup_environment(args: argparse.Namespace) -> None:
    """
    Настройка окружения для обучения.

    Args:
        args: Аргументы командной строки
    """
    # Устанавливаем seed для воспроизводимости
    np.random.seed(args.seed)

    # Создаем директорию для сохранения, если не существует
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Настройка окружения:")
    print(f"  Seed: {args.seed}")
    print(f"  Выходная директория: {args.output_dir}")
    print(f"  Количество слияний: {args.num_merges}")
    print(f"  Доля валидации: {args.val_split}")


def load_corpus(filepath: str) -> List[str]:
    """
    Загрузка корпуса из файла.

    Args:
        filepath: Путь к файлу с корпусом

    Returns:
        List[str]: Список строк корпуса
    """
    print(f"\nЧтение корпуса из {filepath}...")

    if not os.path.exists(filepath):
        print(f"Ошибка: Файл {filepath} не найден!")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Прочитано {len(lines)} строк")
    return lines


def split_train_val(corpus: List[str], val_split: float) -> Tuple[List[str], List[str]]:
    """
    Разделение корпуса на обучающую и валидационную выборки.

    Args:
        corpus: Весь корпус
        val_split: Доля валидационной выборки

    Returns:
        Tuple[List[str], List[str]]: (train_corpus, val_corpus)
    """
    print(f"\nРазделение корпуса...")

    n_total = len(corpus)
    n_val = int(n_total * val_split)
    n_train = n_total - n_val

    print(f"  Всего строк: {n_total}")
    print(f"  Валидация: {n_val} строк ({val_split * 100:.1f}%)")
    print(f"  Обучение: {n_train} строк ({100 - val_split * 100:.1f}%)")

    # Перемешиваем корпус для случайного разбиения
    indices = np.random.permutation(n_total)

    train_indices = indices[:n_train]
    val_indices = indices[n_train:]

    train_corpus = [corpus[i] for i in train_indices]
    val_corpus = [corpus[i] for i in val_indices]

    return train_corpus, val_corpus


def save_corpus_split(corpus: List[str], filepath: str, split_name: str) -> None:
    """
    Сохранение разделенного корпуса в файл.

    Args:
        corpus: Корпус для сохранения
        filepath: Путь для сохранения
        split_name: Название выборки (train/val)
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in corpus:
            f.write(line + '\n')

    print(f"  {split_name} выборка сохранена в: {filepath}")


def train_tokenizer(train_corpus: List[str], num_merges: int) -> BPETokenizer:
    """
    Обучение токенизатора на обучающей выборке.

    Args:
        train_corpus: Обучающая выборка
        num_merges: Количество слияний

    Returns:
        BPETokenizer: Обученный токенизатор
    """
    print(f"\nСоздание токенизатора с {num_merges} слияниями...")

    tokenizer = BPETokenizer(num_merges=num_merges)
    tokenizer.train(train_corpus, verbose=True)

    return tokenizer


def save_model(tokenizer: BPETokenizer, output_dir: str, num_merges: int) -> str:
    """
    Сохранение обученной модели.

    Args:
        tokenizer: Обученный токенизатор
        output_dir: Директория для сохранения
        num_merges: Количество слияний

    Returns:
        str: Путь к сохраненной модели
    """
    model_path = os.path.join(output_dir, f'bpe_model_{num_merges}.json')
    tokenizer.save(model_path)

    return model_path


def validate_tokenizer(tokenizer: BPETokenizer, val_corpus: List[str],
                       num_samples: int = 5) -> bool:
    """
    Проверка токенизатора на валидационной выборке.

    Args:
        tokenizer: Обученный токенизатор
        val_corpus: Валидационная выборка
        num_samples: Количество примеров для проверки

    Returns:
        bool: True если все проверки успешны
    """
    print(f"\nПроверка на валидационной выборке...")

    test_samples = val_corpus[:num_samples]
    all_correct = True

    for i, text in enumerate(test_samples):
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        is_correct = (text == decoded)
        all_correct = all_correct and is_correct

        # Сокращаем текст для отображения
        display_text = text[:50] + "..." if len(text) > 50 else text
        display_decoded = decoded[:50] + "..." if len(decoded) > 50 else decoded

        print(f"\nПример {i + 1}:")
        print(f"  Оригинал: {display_text}")
        print(f"  Декодированный: {display_decoded}")
        print(f"  Совпадение: {'✓' if is_correct else '✗'}")
        print(f"  Длина токенов: {len(ids)}")

    return all_correct


def compute_validation_metrics(tokenizer: BPETokenizer, val_corpus: List[str]) -> Dict:
    """
    Вычисление метрик на валидационной выборке.

    Args:
        tokenizer: Обученный токенизатор
        val_corpus: Валидационная выборка

    Returns:
        Dict: Словарь с метриками
    """
    print(f"\nВычисление метрик на валидационной выборке...")

    lengths = []

    for i, text in enumerate(val_corpus):
        ids = tokenizer.encode(text)
        lengths.append(len(ids))

        if (i + 1) % 500 == 0:
            print(f"  Обработано {i + 1}/{len(val_corpus)} примеров...")

    # Вычисляем статистики
    avg_length = float(np.mean(lengths))
    max_length = int(np.max(lengths))
    min_length = int(np.min(lengths))
    std_length = float(np.std(lengths))

    # Доля очень длинных токенизаций (top-1%)
    percentile_99 = float(np.percentile(lengths, 99))
    long_sequences = [l for l in lengths if l > percentile_99]
    long_percent = float(len(long_sequences) / len(lengths) * 100)

    metrics = {
        'num_merges': tokenizer.num_merges,
        'vocab_size': tokenizer.get_vocab_size(),
        'avg_length': avg_length,
        'min_length': min_length,
        'max_length': max_length,
        'std_length': std_length,
        'long_percent': long_percent,
        'percentile_99': percentile_99,
        'val_size': len(val_corpus)
    }

    return metrics


def save_metrics(metrics: Dict, output_dir: str, num_merges: int) -> str:
    """
    Сохранение метрик в файл.

    Args:
        metrics: Словарь с метриками
        output_dir: Директория для сохранения
        num_merges: Количество слияний

    Returns:
        str: Путь к файлу с метриками
    """
    metrics_path = os.path.join(output_dir, f'metrics_{num_merges}.json')

    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return metrics_path


def print_final_summary(tokenizer: BPETokenizer, metrics: Dict,
                        model_path: str, metrics_path: str,
                        validation_success: bool) -> None:
    """
    Вывод итоговой сводки по обучению.

    Args:
        tokenizer: Обученный токенизатор
        metrics: Вычисленные метрики
        model_path: Путь к сохраненной модели
        metrics_path: Путь к сохраненным метрикам
        validation_success: Результат проверки валидации
    """
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СВОДКА")
    print("=" * 60)

    # Статистика токенизатора
    stats = tokenizer.get_stats()
    print(f"\nСтатистика токенизатора:")
    print(f"  Размер словаря: {stats['vocab_size']}")
    print(f"  Количество слияний: {stats['num_merges']}")

    # Метрики на валидации
    print(f"\nМетрики на валидации:")
    print(f"  Средняя длина: {metrics['avg_length']:.2f} токенов")
    print(f"  Минимальная длина: {metrics['min_length']} токенов")
    print(f"  Максимальная длина: {metrics['max_length']} токенов")
    print(f"  Стандартное отклонение: {metrics['std_length']:.2f}")
    print(f"  99-й перцентиль: {metrics['percentile_99']:.2f}")
    print(f"  Доля очень длинных (top-1%): {metrics['long_percent']:.2f}%")

    # Проверка восстановления
    print(f"\nПроверка восстановления:")
    if validation_success:
        print(f"  ✓ Все проверки пройдены успешно!")
        print(f"  ✓ decode(encode(text)) == text для всех тестовых примеров")
    else:
        print(f"  ✗ Некоторые проверки не пройдены!")

    # Сохраненные файлы
    print(f"\nСохраненные файлы:")
    print(f"  Модель: {model_path}")
    print(f"  Метрики: {metrics_path}")

    print("\n" + "=" * 60)


def main():
    """
    Основная функция скрипта.
    """
    # 1. Парсинг аргументов
    args = parse_arguments()

    # 2. Настройка окружения
    setup_environment(args)

    # 3. Загрузка корпуса
    corpus = load_corpus(args.input_file)

    if len(corpus) == 0:
        print("Ошибка: корпус пуст или файл не найден!")
        return

    # 4. Разделение на train/val
    train_corpus, val_corpus = split_train_val(corpus, args.val_split)

    # 5. Сохранение разделенных данных
    save_corpus_split(train_corpus,
                      os.path.join(args.output_dir, 'train.txt'),
                      'Обучающая')
    save_corpus_split(val_corpus,
                      os.path.join(args.output_dir, 'val.txt'),
                      'Валидационная')

    # 6. Обучение токенизатора
    tokenizer = train_tokenizer(train_corpus, args.num_merges)

    # 7. Сохранение модели
    model_path = save_model(tokenizer, args.output_dir, args.num_merges)

    # 8. Проверка на валидации
    validation_success = validate_tokenizer(tokenizer, val_corpus)

    # 9. Вычисление метрик
    metrics = compute_validation_metrics(tokenizer, val_corpus)

    # 10. Сохранение метрик
    metrics_path = save_metrics(metrics, args.output_dir, args.num_merges)

    # 11. Вывод итоговой сводки
    print_final_summary(tokenizer, metrics, model_path, metrics_path,
                        validation_success)


if __name__ == '__main__':
    main()
