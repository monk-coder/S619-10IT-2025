import os
from pathlib import Path
import chardet


def check_file_encoding(file_path):
    """Проверка кодировки файла"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'], raw_data[:100]  # первые 100 байт


def main():
    data_path = Path("data/raw/data.txt")
    abs_path = data_path.absolute()

    print(f"Проверка файла: {abs_path}")
    print(f"Файл существует: {data_path.exists()}")

    if data_path.exists():
        print(f"Размер файла: {data_path.stat().st_size} байт")

        # Проверка кодировки
        try:
            encoding, preview = check_file_encoding(data_path)
            print(f"Определенная кодировка: {encoding}")
            print(f"Первые 100 байт (hex): {preview.hex()}")
        except Exception as e:
            print(f"Ошибка при определении кодировки: {e}")

        # Попытка прочитать с разными кодировками
        encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1251', 'cp1252', 'latin-1', 'utf-16', 'utf-16-le', 'utf-16-be']

        print("\nПопытка чтения с разными кодировками:")
        for enc in encodings_to_try:
            try:
                with open(data_path, 'r', encoding=enc) as f:
                    lines = [line.strip() for line in f if line.strip()]
                    print(f"  {enc}: {len(lines)} строк")
                    if lines:
                        print(f"    Первая строка: {lines[0][:100]}")
                        break
            except UnicodeDecodeError:
                print(f"  {enc}: ❌ ошибка декодирования")
            except Exception as e:
                print(f"  {enc}: ❌ {e}")
    else:
        print("Файл не найден! Создаю тестовый файл...")

        # Создание тестового файла
        test_data = [
            "Это первый пример текста для обучения токенизатора.",
            "BPE алгоритм используется в современных NLP моделях.",
            "Сегодня хорошая погода для программирования на Python.",
            "Машинное обучение и обработка естественного языка.",
            "Токенизация важный этап в обработке текстов."
        ]

        # Создаем папку если её нет
        data_path.parent.mkdir(parents=True, exist_ok=True)

        # Записываем файл в UTF-8
        with open(data_path, 'w', encoding='utf-8') as f:
            for line in test_data:
                f.write(line + '\n')

        print("Тестовый файл создан!")

        # Проверяем созданный файл
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            print(f"Создано {len(lines)} строк")
            for i, line in enumerate(lines[:3]):
                print(f"  {i + 1}. {line}")


if __name__ == "__main__":
    main()