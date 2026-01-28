import numpy as np
import struct
import os
from urllib.request import urlretrieve
import gzip


def load_mnist():
    """Загрузка датасета MNIST с альтернативного источника"""
    # Используем альтернативный URL
    base_url = 'https://storage.googleapis.com/cvdf-datasets/mnist/'
    files = {
        'train-images-idx3-ubyte': 'train-images-idx3-ubyte.gz',
        'train-labels-idx1-ubyte': 'train-labels-idx1-ubyte.gz',
        't10k-images-idx3-ubyte': 't10k-images-idx3-ubyte.gz',
        't10k-labels-idx1-ubyte': 't10k-labels-idx1-ubyte.gz'
    }

    # Скачивание файлов
    for filename, url_name in files.items():
        if not os.path.exists(filename):
            print(f"Скачивание {filename}...")
            url = base_url + url_name
            try:
                urlretrieve(url, filename + '.gz')
                # Распаковка
                with gzip.open(filename + '.gz', 'rb') as f_in:
                    with open(filename, 'wb') as f_out:
                        f_out.write(f_in.read())
                print(f"  {filename} загружен")
            except Exception as e:
                print(f"Ошибка при загрузке {filename}: {e}")
                # Если не удалось скачать, попробуем другой источник
                return load_mnist_fallback()

    return load_mnist_from_files()


def load_mnist_fallback():
    """Альтернативный способ загрузки MNIST через Keras/TensorFlow"""
    print("Используем альтернативный способ загрузки...")
    try:
        # Пробуем загрузить через tensorflow/keras
        from tensorflow import keras
        (X_train, y_train), (X_test, y_test) = keras.datasets.mnist.load_data()

        # Преобразование формы
        X_train = X_train.reshape(-1, 784) / 255.0
        X_test = X_test.reshape(-1, 784) / 255.0

        print("Данные успешно загружены через TensorFlow")
        return X_train, y_train, X_test, y_test
    except ImportError:
        print("TensorFlow не установлен, используем локальные данные...")
        # Генерация случайных данных для тестирования (если ничего не работает)
        return generate_dummy_data()


def load_mnist_from_files():
    """Загрузка данных из уже скачанных файлов"""
    # Загрузка тренировочных изображений
    with open('train-images-idx3-ubyte', 'rb') as f:
        magic, num, rows, cols = struct.unpack(">IIII", f.read(16))
        X_train = np.fromfile(f, dtype=np.uint8).reshape(num, rows * cols)

    # Загрузка тренировочных меток
    with open('train-labels-idx1-ubyte', 'rb') as f:
        magic, num = struct.unpack(">II", f.read(8))
        y_train = np.fromfile(f, dtype=np.uint8)

    # Загрузка тестовых изображений
    with open('t10k-images-idx3-ubyte', 'rb') as f:
        magic, num, rows, cols = struct.unpack(">IIII", f.read(16))
        X_test = np.fromfile(f, dtype=np.uint8).reshape(num, rows * cols)

    # Загрузка тестовых меток
    with open('t10k-labels-idx1-ubyte', 'rb') as f:
        magic, num = struct.unpack(">II", f.read(8))
        y_test = np.fromfile(f, dtype=np.uint8)

    # Нормализация
    X_train = X_train / 255.0
    X_test = X_test / 255.0

    print(f"Загружено: {X_train.shape[0]} тренировочных и {X_test.shape[0]} тестовых образцов")
    return X_train, y_train, X_test, y_test


def generate_dummy_data():
    """Генерация тестовых данных, если не удалось скачать MNIST"""
    print("Генерация тестовых данных...")
    np.random.seed(42)

    # Маленький набор для тестирования
    X_train = np.random.rand(1000, 784)
    y_train = np.random.randint(0, 10, 1000)
    X_test = np.random.rand(200, 784)
    y_test = np.random.randint(0, 10, 200)

    print("Внимание: используются случайные данные для тестирования!")
    return X_train, y_train, X_test, y_test


def one_hot_encode(y, num_classes=10):
    """One-hot кодирование меток"""
    return np.eye(num_classes)[y]


def plot_training_history(history):
    """Построение графиков обучения"""
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 4))

    # График функции потерь
    plt.subplot(1, 2, 1)
    plt.plot(history['loss'], label='Training Loss')
    if 'val_loss' in history and history['val_loss']:
        plt.plot(history['val_loss'], label='Validation Loss')
    plt.title('Loss Function')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)

    # График точности
    plt.subplot(1, 2, 2)
    plt.plot(history['accuracy'], label='Training Accuracy')
    if 'val_accuracy' in history and history['val_accuracy']:
        plt.plot(history['val_accuracy'], label='Validation Accuracy')
    plt.title('Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('training_history.png')
    plt.show()


def save_results(model, history, accuracy):
    """Сохранение результатов"""
    with open('results.txt', 'w') as f:
        f.write(f"Test Accuracy: {accuracy:.2%}\n")
        f.write(f"Final Training Loss: {history['loss'][-1]:.4f}\n")
        if history.get('val_loss'):
            f.write(f"Final Validation Loss: {history['val_loss'][-1]:.4f}\n")
        f.write(f"\nModel Architecture:\n")
        f.write(f"Input layer: {model.input_size} neurons\n")
        f.write(f"Hidden layer: {model.hidden_size} neurons\n")
        f.write(f"Output layer: {model.output_size} neurons\n")

    print(f"\nResults saved to results.txt")
    print(f"Training history plot saved to training_history.png")
