import numpy as np
from neural_network import NeuralNetwork
from utils import load_mnist, plot_training_history, save_results


def main():
    print("=" * 60)
    print("Нейронная сеть для классификации MNIST")
    print("=" * 60)

    # Загрузка данных
    print("\n1. Загрузка датасета MNIST...")
    X_train, y_train, X_test, y_test = load_mnist()

    # Разделение на тренировочную и валидационную выборки
    n_val = min(10000, len(X_train) // 5)
    X_val = X_train[:n_val]
    y_val = y_train[:n_val]
    X_train = X_train[n_val:]
    y_train = y_train[n_val:]

    print(f"   Тренировочные данные: {X_train.shape[0]} образцов")
    print(f"   Валидационные данные: {X_val.shape[0]} образцов")
    print(f"   Тестовые данные: {X_test.shape[0]} образцов")

    # Параметры обучения
    input_size = X_train.shape[1]
    hidden_size = 128
    output_size = 10
    learning_rate = 0.1
    epochs = 30  # Уменьшено для быстрого тестирования
    batch_size = 32

    print("\n2. Создание нейронной сети...")
    print(f"   Архитектура: {input_size} → {hidden_size} → {output_size}")

    nn = NeuralNetwork(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        learning_rate=learning_rate
    )

    # Обучение
    print("\n3. Обучение модели...")
    history = nn.train(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        epochs=epochs,
        batch_size=batch_size,
        verbose=True
    )

    # Тестирование
    print("\n4. Оценка на тестовой выборке...")
    test_loss, test_accuracy = nn.evaluate(X_test, y_test)
    print(f"   Тестовая точность: {test_accuracy:.2%}")

    # Графики
    print("\n5. Построение графиков...")
    plot_training_history(history)

    # Результаты
    save_results(nn, history, test_accuracy)

    # Демонстрация
    if len(X_test) >= 10:
        predictions = nn.predict(X_test[:10])
        print(f"\nПримеры предсказаний:")
        print(f"  Предсказано: {predictions}")
        print(f"  Фактически:   {y_test[:10]}")

    print("\n" + "=" * 60)
    print("Обучение завершено!")
    print("=" * 60)


if __name__ == "__main__":
    main()