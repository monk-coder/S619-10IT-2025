import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import gzip
import urllib.request
from pathlib import Path
from sklearn.preprocessing import LabelBinarizer

from neural_network import NeuralNetwork


def load_mnist_local():
    """Загрузка MNIST с локального диска или скачивание при отсутствии"""
    base_url = "http://yann.lecun.com/exdb/mnist/"
    files = {
        'train_images': 'train-images-idx3-ubyte.gz',
        'train_labels': 'train-labels-idx1-ubyte.gz',
        'test_images': 't10k-images-idx3-ubyte.gz',
        'test_labels': 't10k-labels-idx1-ubyte.gz'
    }

    data_dir = Path("mnist_data")
    data_dir.mkdir(exist_ok=True)

    # Скачиваем файлы
    for key, filename in files.items():
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"Скачивание {filename}...")
            urllib.request.urlretrieve(base_url + filename, filepath)

    # Функция для чтения файлов
    def read_images(filename):
        with gzip.open(filename, 'rb') as f:
            f.read(4)  # magic number
            num_images = int.from_bytes(f.read(4), 'big')
            rows = int.from_bytes(f.read(4), 'big')
            cols = int.from_bytes(f.read(4), 'big')

            buffer = f.read(rows * cols * num_images)
            data = np.frombuffer(buffer, dtype=np.uint8)
            data = data.reshape(num_images, rows, cols)
            return data

    def read_labels(filename):
        with gzip.open(filename, 'rb') as f:
            f.read(4)  # magic number
            num_items = int.from_bytes(f.read(4), 'big')

            buffer = f.read(num_items)
            data = np.frombuffer(buffer, dtype=np.uint8)
            return data

    # Загружаем данные
    train_images = read_images(data_dir / files['train_images'])
    train_labels = read_labels(data_dir / files['train_labels'])
    test_images = read_images(data_dir / files['test_images'])
    test_labels = read_labels(data_dir / files['test_labels'])

    return train_images, train_labels, test_images, test_labels


def prepare_data(validation_size=5000):
    """Подготовка данных для обучения"""
    print("Загрузка данных MNIST...")

    # Загружаем данные
    train_images, train_labels, test_images, test_labels = load_mnist_local()

    # Объединяем для разделения
    all_images = np.vstack([train_images, test_images])
    all_labels = np.hstack([train_labels, test_labels])

    # Преобразуем изображения в вектор и нормализуем
    X = all_images.reshape(-1, 28 * 28).T.astype('float32') / 255.0
    y = all_labels.astype('int32')

    # One-hot encoding
    lb = LabelBinarizer()
    y_onehot = lb.fit_transform(y).T

    # Разделяем на train/val/test
    n_samples = X.shape[1]

    # Тестовая выборка (последние 10000 примеров)
    X_test = X[:, -10000:]
    y_test = y_onehot[:, -10000:]
    y_test_labels = y[-10000:]

    # Оставшиеся данные
    X_remaining = X[:, :-10000]
    y_remaining = y_onehot[:, :-10000]
    y_remaining_labels = y[:-10000]

    # Разделяем оставшиеся на train и validation
    n_remaining = X_remaining.shape[1]
    indices = np.random.permutation(n_remaining)

    X_remaining = X_remaining[:, indices]
    y_remaining = y_remaining[:, indices]
    y_remaining_labels = y_remaining_labels[indices]

    # Валидационная выборка
    X_val = X_remaining[:, :validation_size]
    y_val = y_remaining[:, :validation_size]
    y_val_labels = y_remaining_labels[:validation_size]

    # Обучающая выборка
    X_train = X_remaining[:, validation_size:]
    y_train = y_remaining[:, validation_size:]

    print(f"Размеры выборок: обучающая={X_train.shape[1]}, валидационная={X_val.shape[1]}, тестовая={X_test.shape[1]}")

    return (X_train, y_train,
            X_val, y_val,
            X_test, y_test,
            y_val_labels, y_test_labels)


def plot_training_history(history, save_path='training_history.png'):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].plot(history['train_loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Validation Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)

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

    hidden_sizes = [int(x) for x in args.hidden_layers.split(',')]

    # Загрузка данных
    X_train, y_train, X_val, y_val, X_test, y_test, y_val_labels, y_test_labels = prepare_data()

    # Создание нейронной сети
    layer_sizes = [784] + hidden_sizes + [10]
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

    # Примеры предсказаний
    print("\nПримеры предсказаний на валидационном наборе:")
    sample_indices = np.random.choice(X_val.shape[1], 5, replace=False)
    predictions = model.predict(X_val[:, sample_indices])

    for i, idx in enumerate(sample_indices[:3]):
        true_label = np.argmax(y_val[:, idx])
        print(f"Пример {i + 1}: Предсказано {predictions[i]}, Истинное значение {true_label}")


if __name__ == "__main__":
    main()   
