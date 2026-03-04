#!/usr/bin/env python3
import subprocess
import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python run.py train                 # Обучение модели")
        print("  python run.py sample --prompt '...' # Генерация текста")
        print("  python run.py test                   # Запуск тестов")
        return

    command = sys.argv[1]

    if command == 'train':
        print("Запуск обучения...")
        subprocess.run([sys.executable, 'train.py'])

    elif command == 'sample':
        print("Запуск генерации...")
        subprocess.run([sys.executable, 'sample.py'] + sys.argv[2:])

    elif command == 'test':
        print("Запуск тестов...")
        subprocess.run([sys.executable, '-m', 'pytest', 'tests/'])

    else:
        print(f"Неизвестная команда: {command}")
        print("Доступные команды: train, sample, test")


if __name__ == "__main__":
    main()