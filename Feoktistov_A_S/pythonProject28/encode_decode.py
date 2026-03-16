#!/usr/bin/env python3
"""
Скрипт для кодирования и декодирования текста с помощью обученного BPE токенизатора.
"""

import argparse
import os
import sys
import json

# Добавляем путь к текущей директории для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenizer import BPETokenizer


def interactive_mode(tokenizer: BPETokenizer):
    """
    Интерактивный режим для кодирования/декодирования текста.

    Args:
        tokenizer: Загруженный токенизатор
    """
    print("\n" + "=" * 60)
    print("Интерактивный режим BPE токенизатора")
    print("Введите текст для кодирования или 'exit' для выхода")
    print("=" * 60)

    while True:
        try:
            text = input("\nВведите текст: ").strip()

            if text.lower() in ['exit', 'quit', 'выход']:
                print("Выход из программы...")
                break

            if not text:
                print("Введите непустой текст")
                continue

            # Кодируем текст
            ids = tokenizer.encode(text)

            # Декодируем обратно
            decoded = tokenizer.decode(ids)

            # Проверяем совпадение
            is_correct = (text == decoded)

            # Выводим результаты
            print("\n" + "-" * 60)
            print(f"Оригинальный текст: {text}")
            print(f"Количество токенов: {len(ids)}")
            print(f"ID токенов: {ids}")

            # Показываем только первые 10 id для краткости
            if len(ids) > 10:
                print(f"Первые 10 ID: {ids[:10]}...")

            print(f"\nДекодированный текст: {decoded}")
            print(f"Совпадение: {'✓' if is_correct else '✗'}")

            if not is_correct:
                print("\nПредупреждение: Текст не восстановлен идеально!")
                print("Это может быть из-за символов, не вошедших в словарь.")

            # Показываем примеры токенов
            print(f"\nПримеры токенов:")
            for i, id_ in enumerate(ids[:5]):  # Показываем первые 5 токенов
                if id_ in tokenizer.vocab:
                    token = tokenizer.vocab[id_]
                    # Заменяем специальный символ для отображения
                    display_token = token.replace('Ġ', '[SPACE]')
                    print(f"  ID {id_}: '{display_token}'")
                else:
                    print(f"  ID {id_}: <UNKNOWN>")

            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\nВыход из программы...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")


def batch_mode(tokenizer: BPETokenizer, input_file: str, output_file: str):
    """
    Пакетный режим для кодирования файла.

    Args:
        tokenizer: Загруженный токенизатор
        input_file: Входной файл
        output_file: Выходной файл
    """
    print(f"Пакетное кодирование файла {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    results = []

    for i, line in enumerate(lines):
        ids = tokenizer.encode(line)
        decoded = tokenizer.decode(ids)

        results.append({
            'text': line,
            'ids': ids,
            'decoded': decoded,
            'length': len(ids),
            'correct': line == decoded
        })

        if (i + 1) % 100 == 0:
            print(f"Обработано {i + 1}/{len(lines)} строк...")

    # Сохраняем результаты
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Вычисляем статистику
    total_correct = sum(1 for r in results if r['correct'])
    avg_length = sum(r['length'] for r in results) / len(results)

    print(f"\nПакетное кодирование завершено!")
    print(f"Обработано строк: {len(lines)}")
    print(f"Успешно восстановлено: {total_correct}/{len(lines)} ({total_correct / len(lines) * 100:.2f}%)")
    print(f"Средняя длина: {avg_length:.2f} токенов")
    print(f"Результаты сохранены в: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Кодирование и декодирование текста с помощью BPE')
    parser.add_argument('--model_dir', type=str, default='./models',
                        help='Директория с сохраненной моделью (по умолчанию: ./models)')
    parser.add_argument('--num_merges', type=int, default=8000,
                        help='Количество слияний модели для загрузки (по умолчанию: 8000)')
    parser.add_argument('--mode', type=str, choices=['interactive', 'batch'], default='interactive',
                        help='Режим работы: interactive или batch (по умолчанию: interactive)')
    parser.add_argument('--input_file', type=str,
                        help='Входной файл для пакетного режима')
    parser.add_argument('--output_file', type=str, default='encoded_results.json',
                        help='Выходной файл для пакетного режима (по умолчанию: encoded_results.json)')

    args = parser.parse_args()

    # Определяем путь к модели
    model_path = os.path.join(args.model_dir, f'bpe_model_{args.num_merges}.json')

    if not os.path.exists(model_path):
        print(f"Ошибка: Файл модели {model_path} не найден!")
        print("Сначала обучите модель с помощью train.py")
        return

    # Загружаем токенизатор
    print(f"Загрузка токенизатора из {model_path}...")
    tokenizer = BPETokenizer.load(model_path)

    # Выводим информацию о токенизаторе
    stats = tokenizer.get_stats()
    print(f"Загружен токенизатор со статистикой:")
    print(f"  Размер словаря: {stats['vocab_size']}")
    print(f"  Количество слияний: {stats['num_merges']}")

    # Выбираем режим работы
    if args.mode == 'interactive':
        interactive_mode(tokenizer)
    elif args.mode == 'batch':
        if not args.input_file:
            print("Ошибка: Для пакетного режима необходимо указать --input_file")
            return

        if not os.path.exists(args.input_file):
            print(f"Ошибка: Входной файл {args.input_file} не найден!")
            return

        batch_mode(tokenizer, args.input_file, args.output_file)


if __name__ == '__main__':
    main()