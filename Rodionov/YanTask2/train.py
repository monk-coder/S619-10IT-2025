import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
import argparse
import os

from neural_network import NeuralNetwork

def load_mnist_data():
    """
    Загрузка и подготовка данных MNIST
    """
    print("Загрузка данных MNIST...")

    # Загрузка данных
    mnist = fetch_openml('mnist_784', version=1, parser='auto')

    # Преобразование данных
    X = mnist.data.values.astype('float32').T  # Транспонируем для формата (features, samples)
    y = mnist.target.values.astype('int32')

    # Нормализация пикселей в диапазон [0, 1]
    X = X / 255.0

    # One-hot encoding меток
    lb = LabelBinarizer()
    y_onehot = lb.fit_transform(y).T

    # Разделение на обучающую и тестовую выборки
    X_train, X_temp, y_train, y_temp = train_test_split(
        X.T, y_onehot.T, test_size=0.3, random_state=42, stratify=y
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp.argmax(axis=1)
    )

    # Возвращаем в транспонированном виде
    return (X_train.T, y_train.T,
            X_val.T, y_val.T,
            X_test.T, y_test.T,
            y[y_train.shape[0]:y_train.shape[0]+y_val.shape[0]])

def plot_training_history(history, save_path='training_history.png'):
    """
    Визуализация истории обучения

    Parameters:
    -----------
    history : dict
        История обучения, возвращаемая методом train
    save_path : str
        Путь для сохранения графика
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # График потерь
    axes[0].plot(history['train_loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Validation Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)

    # График точности
    axes[1].plot(history['train_accuracy'], label='Train Accuracy')
    axes[1].plot(history['val_accuracy'], label='Validation Accuracy')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Обучение нейронной сети на MNIST')
    parser.add_argument('--epochs', type=int, default=20,
                       help='Количество эпох обучения')
    parser.add_argument('--learning_rate', type=float, default=0.01,
                       help='Скорость обучения')
    parser.add_argument('--batch_size', type=int, default=64,
                       help='Размер мини-батча')
    parser.add_argument('--regularization', type=float, default=0.001,
                       help='Коэффициент L2 регуляризации')
    parser.add_argument('--hidden_layers', type=str, default='128,64',
                       help='Размеры скрытых слоев через запятую')
    parser.add_argument('--save_model', type=str, default='mnist_model.pkl',
                       help='Путь для сохранения обученной модели')

    args = parser.parse_args()

    # Парсинг размеров скрытых слоев
    hidden_sizes = [int(x) for x in args.hidden_layers.split(',')]

    # Загрузка данных
    X_train, y_train, X_val, y_val, X_test, y_test, y_val_labels = load_mnist_data()

    print(f"Размеры выборок: обучающая={X_train.shape[1]}, валидационная={X_val.shape[1]}, тестовая={X_test.shape[1]}")

    # Создание нейронной сети
    layer_sizes = [784] + hidden_sizes + [10]  # 784 входных нейрона, 10 выходных
    print(f"Архитектура сети: {layer_sizes}")

    model = NeuralNetwork(
        layer_sizes=layer_sizes,
        learning_rate=args.learning_rate,
        regularization=args.regularization
    )

    # Обучение модели
    history = model.train(
        X_train=X_train,
        Y_train=y_train,
        X_val=X_val,
        Y_val=y_val,
        epochs=args.epochs,
        batch_size=args.batch_size
    )

    # Сохранение модели
    model.save_model(args.save_model)

    # Визуализация истории обучения
    plot_training_history(history)

    # Оценка на тестовом наборе
    test_accuracy = model.accuracy(X_test, y_test)
    print(f"\nТочность на тестовом наборе: {test_accuracy:.4f}")

    # Вывод примера предсказаний
    print("\nПримеры предсказаний на валидационном наборе:")
    sample_indices = np.random.choice(X_val.shape[1], 10, replace=False)
    predictions = model.predict(X_val[:, sample_indices])

    for i, idx in enumerate(sample_indices[:5]):
        true_label = np.argmax(y_val[:, idx])
        print(f"Пример {i+1}: Предсказано {predictions[i]}, Истинное значение {true_label}")

if __name__ == "__main__":
    main()