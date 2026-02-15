import os
from pathlib import Path

print(f"Текущая директория: {os.getcwd()}")

data_path = Path("data/raw/data.txt")
full_path = data_path.absolute()

print(f"Полный путь к файлу: {full_path}")
print(f"Файл существует: {data_path.exists()}")

if not data_path.exists():
    print("\nСоздаю папки и файл...")
    data_path.parent.mkdir(parents=True, exist_ok=True)

    test_data = '''Это первый пример текста для обучения токенизатора.
BPE алгоритм используется в современных NLP моделях.
Сегодня хорошая погода для программирования на Python.
Машинное обучение и обработка естественного языка.
Токенизация важный этап в обработке текстов.'''

    with open(data_path, 'w', encoding='utf-8') as f:
        f.write(test_data)

    print(f"Файл создан! Размер: {data_path.stat().st_size} байт")
    print("\nСодержимое файла:")
    with open(data_path, 'r', encoding='utf-8') as f:
        print(f.read())