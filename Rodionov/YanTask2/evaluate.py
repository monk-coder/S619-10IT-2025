import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import argparse

from neural_network import NeuralNetwork

# Импортируем функцию prepare_data из train.py
try:
    from train import prepare_data
except ImportError:
    # Если не получается импортировать, определим здесь
    import gzip
    import urllib.request
    from pathlib import Path
    from sklearn.preprocessing import LabelBinarizer


    def prepare_data(validation_size=5000):
        """Та же функция что и в train.py"""
        base_url = "http://yann.lecun.com/exdb/mnist/"
        files = {
            'train_images': 'train-images-idx3-ubyte.gz',
            'train_labels': 'train-labels-idx1-ubyte.gz',
            'test_images': 't10k-images-idx3-ubyte.gz',
            'test_labels': 't10k-labels-idx1-ubyte.gz'
        }

        data_dir = Path("mnist_data")
        data_dir.mkdir(exist_ok=True)

        for key, filename in files.items():
            filepath = data_dir / filename
            if not filepath.exists():
                print(f"Скачивание {filename}...")
                urllib.request.urlretrieve(base_url + filename, filepath)

        def read_images(filename):
            with gzip.open(filename, 'rb') as f:
                f.read(4)
                num_images = int.from_bytes(f.read(4), 'big')
                rows = int.from_bytes(f.read(4), 'big')
                cols = int.from_bytes(f.read(4), 'big')
                buffer = f.read(rows * cols * num_images)
                data = np.frombuffer(buffer, dtype=np.uint8)
                return data.reshape(num_images, rows, cols)

        def read_labels(filename):
            with gzip.open(filename, 'rb') as f:
                f.read(4)
                num_items = int.from_bytes(f.read(4), 'big')
                buffer = f.read(num_items)
                return np.frombuffer(buffer, dtype=np.uint8)

        train_images = read_images(data_dir / files['train_images'])
        train_labels = read_labels(data_dir / files['train_labels'])
        test_images = read_images(data_dir / files['test_images'])
        test_labels = read_labels(data_dir / files['test_labels'])

        all_images = np.vstack([train_images, test_images])
        all_labels = np.hstack([train_labels, test_labels])

        X = all_images.reshape(-1, 28 * 28).T.astype('float32') / 255.0
        y = all_labels.astype('int32')

        lb = LabelBinarizer()
        y_onehot = lb.fit_transform(y).T

        X_test = X[:, -10000:]
        y_test = y_onehot[:, -10000:]
        y_test_labels = y[-10000:]

        X_remaining = X[:, :-10000]
        y_remaining = y_onehot[:, :-10000]
        y_remaining_labels = y[:-10000]

        n_remaining = X_remaining.shape[1]
        indices = np.random.permutation(n_remaining)

        X_remaining = X_remaining[:, indices]
        y_remaining = y_remaining[:, indices]
        y_remaining_labels = y_remaining_labels[indices]

        X_val = X_remaining[:, :validation_size]
        y_val = y_remaining[:, :validation_size]
        y_val_labels = y_remaining_labels[:validation_size]

        X_train = X_remaining[:, validation_size:]
        y_train = y_remaining[:, validation_size:]

        return (X_train, y_train, X_val, y_val, X_test, y_test, y_val_labels, y_test_labels)


def plot_confusion_matrix(y_true, y_pred, save_path='confusion_matrix.png'):
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    return cm


def plot_sample_predictions(model, X, y_true, y_pred, save_path='sample_predictions.png'):
    num_samples = 10
    sample_indices = np.random.choice(X.shape[1], num_samples, replace=False)

    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.ravel()

    for i, idx in enumerate(sample_indices):
        image = X[:, idx].reshape(28, 28)

        activations, _ = model.forward_propagation(X[:, idx:idx + 1])
        probs = activations[-1][:, 0]

        axes[i].imshow(image, cmap='gray')
        axes[i].axis('off')

        true_label = y_true[idx]
        pred_label = y_pred[idx]

        color = 'green' if true_label == pred_label else 'red'
        axes[i].set_title(f'True: {true_label}\nPred: {pred_label}\nProb: {probs[pred_label]:.2f}',
                          color=color, fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Оценка обученной модели на MNIST')
    parser.add_argument('--model_path', type=str, default='mnist_model.pkl',
                        help='Путь к сохраненной модели')

    args = parser.parse_args()

    # Загрузка данных (только нужные части)
    _, _, X_val, y_val, X_test, y_test, y_val_labels, _ = prepare_data()

    # Загрузка модели
    print(f"Загрузка модели из {args.model_path}")
    model = NeuralNetwork.load_model(args.model_path)

    # Предсказания на валидационном наборе
    print("\nОценка на валидационном наборе:")
    val_predictions = model.predict(X_val)
    val_accuracy = model.accuracy(X_val, y_val)
    print(f"Точность на валидационном наборе: {val_accuracy:.4f}")

    # Матрица ошибок
    cm = plot_confusion_matrix(y_val_labels, val_predictions)

    # Отчет классификации
    print("\nОтчет классификации:")
    print(classification_report(y_val_labels, val_predictions,
                                target_names=[str(i) for i in range(10)]))

    # Визуализация примеров
    plot_sample_predictions(model, X_val, y_val_labels, val_predictions)

    # Оценка на тестовом наборе
    print("\nОценка на тестовом наборе:")
    test_predictions = model.predict(X_test)
    test_accuracy = model.accuracy(X_test, y_test)
    print(f"Точность на тестовом наборе: {test_accuracy:.4f}")


if __name__ == "__main__":
    main()