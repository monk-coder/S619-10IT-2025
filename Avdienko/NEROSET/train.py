#!/usr/bin/env python3
"""
Скрипт для обучения нейронной сети на MNIST
"""

import numpy as np
import matplotlib.pyplot as plt
from mnist_nn import NeuralNetwork, load_mnist, plot_training_history, create_train_val_split, download_mnist
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description='Обучение нейронной сети на MNIST')
    parser.add_argument('--epochs', type=int, default=30, help='Количество эпох')
    parser.add_argument('--batch_size', type=int, default=64, help='Размер батча')
    parser.add_argument('--learning_rate', type=float, default=0.01, help='Скорость обучения')
    parser.add_argument('--hidden_layers', type=str, default='128,64', help='Размеры скрытых слоев через запятую')
    parser.add_argument('--activation', type=str, default='relu', choices=['relu', 'sigmoid', 'tanh'],
                        help='Функция активации')
    parser.add_argument('--reg_lambda', type=float, default=0.001, help='Коэффициент регуляризации L2')
    parser.add_argument('--val_ratio', type=float, default=0.2, help='Доля валидационных данных')
    parser.add_argument('--save_model', type=str, default='mnist_model.pkl', help='Путь для сохранения модели')
    parser.add_argument('--download', action='store_true', help='Скачать датасет MNIST')

    args = parser.parse_args()

    # Скачивание датасета, если нужно
    if args.download:
        print("Скачивание датасета MNIST...")
        download_mnist()

    print("Загрузка датасета MNIST...")
    X_train, Y_train, X_test, Y_test = load_mnist()
    print(f"Размер тренировочных данных: {X_train.shape}")
    print(f"Размер тестовых данных: {X_test.shape}")

    # Разделение на train/validation
    print(f"\nРазделение данных на train/validation ({args.val_ratio * 100}% validation)...")
    X_train_split, Y_train_split, X_val, Y_val = create_train_val_split(
        X_train, Y_train, val_ratio=args.val_ratio
    )
    print(f"Train: {X_train_split.shape[1]} примеров")
    print(f"Validation: {X_val.shape[1]} примеров")

    # Парсинг скрытых слоев
    hidden_layers = [int(x) for x in args.hidden_layers.split(',') if x.strip()]
    layer_sizes = [784] + hidden_layers + [10]  # 784 входа, скрытые слои, 10 выходов

    print(f"\nАрхитектура сети: {layer_sizes}")
    print(f"Параметры обучения:")
    print(f"  Эпохи: {args.epochs}")
    print(f"  Размер батча: {args.batch_size}")
    print(f"  Скорость обучения: {args.learning_rate}")
    print(f"  Функция активации: {args.activation}")
    print(f"  Регуляризация L2: {args.reg_lambda}")

    # Создание и обучение модели
    print("\nСоздание нейронной сети...")
    nn = NeuralNetwork(
        layer_sizes=layer_sizes,
        learning_rate=args.learning_rate,
        activation=args.activation,
        reg_lambda=args.reg_lambda
    )

    print("Начало обучения...")
    start_time = time.time()

    history = nn.train(
        X_train=X_train_split,
        Y_train=Y_train_split,
        X_val=X_val,
        Y_val=Y_val,
        epochs=args.epochs,
        batch_size=args.batch_size,
        verbose=True
    )

    training_time = time.time() - start_time
    print(f"\nОбучение завершено за {training_time:.2f} секунд")

    # Оценка на тестовых данных
    print("\nОценка на тестовых данных...")
    test_predictions = nn.predict(X_test)
    test_labels = np.argmax(Y_test, axis=0)
    test_accuracy = np.mean(test_predictions == test_labels) * 100

    print(f"Точность на тестовых данных: {test_accuracy:.2f}%")

    # Сохранение модели
    if args.save_model:
        print(f"Сохранение модели в {args.save_model}...")
        nn.save_model(args.save_model)

    # Построение графиков
    print("\nПостроение графиков обучения...")
    plot_training_history(history)

    # Вывод примеров предсказаний
    print("\nПримеры предсказаний на тестовых данных:")
    indices = np.random.choice(X_test.shape[1], 10, replace=False)

    fig, axes = plt.subplots(2, 5, figsize=(12, 5))
    axes = axes.ravel()

    for i, idx in enumerate(indices):
        img = X_test[:, idx].reshape(28, 28)
        true_label = test_labels[idx]
        pred_label = test_predictions[idx]

        axes[i].imshow(img, cmap='gray')
        axes[i].axis('off')
        axes[i].set_title(f'True: {true_label}, Pred: {pred_label}',
                          color='green' if true_label == pred_label else 'red')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()