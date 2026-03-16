import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import gzip
import urllib.request
from pathlib import Path
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import confusion_matrix
import seaborn as sns

from neural_network import NeuralNetwork


def load_mnist_local():
    """Загрузка MNIST с локального диска или скачивание при отсутствии"""
    # Альтернативные URL для MNIST
    urls = [
        "https://ossci-datasets.s3.amazonaws.com/mnist/",
        "http://yann.lecun.com/exdb/mnist/",
        "https://storage.googleapis.com/cvdf-datasets/mnist/"
    ]

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
            downloaded = False

            for base_url in urls:
                try:
                    url = base_url + filename
                    urllib.request.urlretrieve(url, filepath)
                    print(f"  Успешно скачан с {base_url}")
                    downloaded = True
                    break
                except Exception as e:
                    print(f"  Ошибка с {base_url}: {e}")
                    continue

            if not downloaded:
                print(f"  Не удалось скачать {filename}")
                return None

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

    try:
        # Загружаем данные
        train_images = read_images(data_dir / files['train_images'])
        train_labels = read_labels(data_dir / files['train_labels'])
        test_images = read_images(data_dir / files['test_images'])
        test_labels = read_labels(data_dir / files['test_labels'])

        return train_images, train_labels, test_images, test_labels
    except Exception as e:
        print(f"Ошибка при чтении файлов: {e}")
        return None


def create_synthetic_data():
    """Создание синтетических данных для теста"""
    print("Создание синтетических данных...")
    np.random.seed(42)

    # Создаем простые паттерны для каждой цифры
    n_samples = 70000
    images = []
    labels = []

    for i in range(n_samples):
        label = np.random.randint(0, 10)
        img = np.zeros((28, 28), dtype=np.float32)

        # Простые паттерны для каждой цифры
        if label == 0:  # Круг
            for x in range(28):
                for y in range(28):
                    dist = np.sqrt((x - 14) ** 2 + (y - 14) ** 2)
                    if 8 < dist < 12:
                        img[x, y] = np.random.uniform(0.7, 1.0)

        elif label == 1:  # Вертикальная линия
            img[8:20, 14] = np.random.uniform(0.7, 1.0, size=12)

        elif label == 2:  # Две дуги
            for x in range(28):
                for y in range(28):
                    if (8 < x < 20 and abs(y - 10) < 2) or (8 < x < 20 and abs(y - 18) < 2):
                        img[x, y] = np.random.uniform(0.7, 1.0)

        else:  # Случайный шум для других цифр
            img = np.random.rand(28, 28) * 0.5

        # Добавляем немного шума
        img += np.random.randn(28, 28) * 0.1
        img = np.clip(img, 0, 1)

        images.append(img)
        labels.append(label)

    return np.array(images), np.array(labels)


def prepare_data(validation_size=5000):
    """Подготовка данных для обучения"""
    print("Загрузка данных MNIST...")

    # Пробуем загрузить реальные данные
    data = load_mnist_local()

    if data is not None:
        train_images, train_labels, test_images, test_labels = data
        all_images = np.vstack([train_images, test_images])
        all_labels = np.hstack([train_labels, test_labels])
        print("  Используются реальные данные MNIST")
    else:
        # Если не получилось, создаем синтетические
        all_images, all_labels = create_synthetic_data()
        print("  Используются синтетические данные")

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

    print(
        f"  Размеры выборок: обучающая={X_train.shape[1]}, валидационная={X_val.shape[1]}, тестовая={X_test.shape[1]}")

    return (X_train, y_train,
            X_val, y_val,
            X_test, y_test,
            y_val_labels, y_test_labels)


def save_plots(model, X_val, y_val_labels, history):
    """Сохранение графиков в файлы"""
    print("\n" + "=" * 60)
    print("СОХРАНЕНИЕ ГРАФИКОВ...")
    print("=" * 60)

    # 1. График обучения
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], 'b-', label='Train Loss', linewidth=2)
    plt.plot(history['val_loss'], 'r-', label='Validation Loss', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Loss during Training')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(history['train_accuracy'], 'b-', label='Train Accuracy', linewidth=2)
    plt.plot(history['val_accuracy'], 'r-', label='Validation Accuracy', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.title('Accuracy during Training')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('training_history.png', dpi=150, bbox_inches='tight')
    print("✅ training_history.png - сохранен")

    # 2. Матрица ошибок
    val_predictions = model.predict(X_val)
    cm = confusion_matrix(y_val_labels, val_predictions)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
    print("✅ confusion_matrix.png - сохранен")

    # 3. Примеры предсказаний
    num_samples = 10
    sample_indices = np.random.choice(X_val.shape[1], num_samples, replace=False)

    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.flatten()

    for i, idx in enumerate(sample_indices):
        image = X_val[:, idx].reshape(28, 28)

        activations, _ = model.forward_propagation(X_val[:, idx:idx + 1])
        probs = activations[-1][:, 0]
        pred_label = np.argmax(probs)
        true_label = y_val_labels[idx]

        axes[i].imshow(image, cmap='gray')
        axes[i].axis('off')

        color = 'green' if true_label == pred_label else 'red'
        axes[i].set_title(f'True: {true_label}\nPred: {pred_label}\nProb: {probs[pred_label]:.2f}',
                          color=color, fontsize=10)

    plt.tight_layout()
    plt.savefig('sample_predictions.png', dpi=150, bbox_inches='tight')
    print("✅ sample_predictions.png - сохранен")

    # Закрываем все фигуры
    plt.close('all')

    # 4. Вывод статистики в консоль
    print("\n" + "=" * 60)
    print("СТАТИСТИКА МОДЕЛИ:")
    print("=" * 60)

    accuracy = np.mean(y_val_labels == val_predictions)
    error_rate = 1 - accuracy

    print(f"Точность на валидации: {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"Ошибка на валидации: {error_rate:.4f} ({error_rate * 100:.1f}%)")
    print(f"Правильных предсказаний: {np.sum(y_val_labels == val_predictions)}/{len(y_val_labels)}")

    # Самые частые ошибки
    error_indices = np.where(y_val_labels != val_predictions)[0]
    if len(error_indices) > 0:
        print(f"\nПримеры ошибок (первые 3):")
        for i in error_indices[:3]:
            print(f"  Истинная: {y_val_labels[i]}, Предсказанная: {val_predictions[i]}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Обучение нейронной сети на MNIST')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Количество эпох обучения (по умолчанию: 10)')
    parser.add_argument('--learning_rate', type=float, default=0.01,
                        help='Скорость обучения (по умолчанию: 0.01)')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Размер мини-батча (по умолчанию: 64)')
    parser.add_argument('--regularization', type=float, default=0.001,
                        help='Коэффициент L2 регуляризации (по умолчанию: 0.001)')
    parser.add_argument('--hidden_layers', type=str, default='128,64',
                        help='Размеры скрытых слоев через запятую (по умолчанию: "128,64")')
    parser.add_argument('--save_model', type=str, default='mnist_model.pkl',
                        help='Путь для сохранения обученной модели (по умолчанию: "mnist_model.pkl")')

    args = parser.parse_args()

    hidden_sizes = [int(x) for x in args.hidden_layers.split(',')]

    # Загрузка данных
    X_train, y_train, X_val, y_val, X_test, y_test, y_val_labels, y_test_labels = prepare_data()

    # Создание нейронной сети
    layer_sizes = [784] + hidden_sizes + [10]
    print(f"\nАрхитектура сети: {layer_sizes}")
    print(f"Параметры обучения: LR={args.learning_rate}, Batch={args.batch_size}, Epochs={args.epochs}")

    model = NeuralNetwork(
        layer_sizes=layer_sizes,
        learning_rate=args.learning_rate,
        regularization=args.regularization
    )

    # Обучение модели
    print("\n" + "=" * 60)
    print("НАЧАЛО ОБУЧЕНИЯ")
    print("=" * 60)

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

    # Сохранение графиков
    save_plots(model, X_val, y_val_labels, history)

    # Оценка на тестовом наборе
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ НА ТЕСТОВОМ НАБОРЕ")
    print("=" * 60)

    test_predictions = model.predict(X_test)
    test_accuracy = np.mean(y_test_labels == test_predictions)

    print(f"Точность на тестовом наборе: {test_accuracy:.4f} ({test_accuracy * 100:.1f}%)")
    print(f"Правильных: {np.sum(y_test_labels == test_predictions)}/{len(y_test_labels)}")

    # Примеры предсказаний в консоль
    print(f"\nПримеры предсказаний на тестовом наборе (5 случайных):")
    sample_indices = np.random.choice(X_test.shape[1], 5, replace=False)

    for i, idx in enumerate(sample_indices):
        true_label = y_test_labels[idx]
        pred_label = test_predictions[idx]
        status = "✓" if true_label == pred_label else "✗"

        print(f"  Пример {i + 1}: Истинная цифра = {true_label}, "
              f"Предсказанная = {pred_label} {status}")

    print("\n" + "=" * 60)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)
    print("Созданы файлы:")
    print("  1. training_history.png    - График обучения")
    print("  2. confusion_matrix.png    - Матрица ошибок")
    print("  3. sample_predictions.png  - Примеры предсказаний")
    print("  4. mnist_model.pkl        - Сохраненная модель")
    print("=" * 60)


if __name__ == "__main__":
    main()