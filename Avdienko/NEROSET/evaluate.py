#!/usr/bin/env python3
"""
Скрипт для оценки обученной модели
"""

import numpy as np
from mnist_nn import NeuralNetwork, load_mnist
import argparse


def main():
    parser = argparse.ArgumentParser(description='Оценка обученной модели на MNIST')
    parser.add_argument('--model_path', type=str, default='mnist_model.pkl',
                        help='Путь к сохраненной модели')
    parser.add_argument('--num_examples', type=int, default=10,
                        help='Количество примеров для визуализации')

    args = parser.parse_args()

    print("Загрузка датасета MNIST...")
    _, _, X_test, Y_test = load_mnist()

    print(f"Загрузка модели из {args.model_path}...")
    nn = NeuralNetwork.load_model(args.model_path)

    print("\nОценка модели на тестовых данных...")

    # Предсказания
    predictions = nn.predict(X_test)
    labels = np.argmax(Y_test, axis=0)

    # Метрики
    accuracy = np.mean(predictions == labels) * 100
    print(f"Общая точность: {accuracy:.2f}%")

    # Матрица ошибок
    confusion_matrix = np.zeros((10, 10), dtype=int)
    for true, pred in zip(labels, predictions):
        confusion_matrix[true, pred] += 1

    print("\nМатрица ошибок:")
    print("(Строки - истинные значения, столбцы - предсказания)")
    print(confusion_matrix)

    # Точность по классам
    print("\nТочность по классам:")
    for i in range(10):
        class_correct = confusion_matrix[i, i]
        class_total = np.sum(confusion_matrix[i, :])
        class_accuracy = class_correct / class_total * 100 if class_total > 0 else 0
        print(f"  Цифра {i}: {class_accuracy:.1f}% ({class_correct}/{class_total})")

    # Примеры ошибок
    print("\nПримеры ошибок классификации:")
    error_indices = np.where(predictions != labels)[0]

    if len(error_indices) > 0:
        num_errors_to_show = min(5, len(error_indices))
        error_samples = error_indices[:num_errors_to_show]

        for i, idx in enumerate(error_samples):
            true_label = labels[idx]
            pred_label = predictions[idx]
            print(f"  Пример {i + 1}: Истинная цифра={true_label}, Предсказанная={pred_label}")


if __name__ == "__main__":
    main()