import numpy as np
import matplotlib.pyplot as plt
import gzip
import os
import pickle
from typing import Tuple, List, Optional


class NeuralNetwork:
    """
    Полносвязная нейронная сеть с возможностью настройки архитектуры
    """

    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.01,
                 activation: str = 'relu', reg_lambda: float = 0.01):
        """
        Инициализация нейронной сети

        Args:
            layer_sizes: список размеров слоев (входной, скрытые, выходной)
            learning_rate: скорость обучения
            activation: функция активации ('relu', 'sigmoid', 'tanh')
            reg_lambda: коэффициент регуляризации L2
        """
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.activation = activation
        self.reg_lambda = reg_lambda
        self.L = len(layer_sizes) - 1  # Количество обучаемых слоев

        # Инициализация весов и смещений
        self.weights = []
        self.biases = []

        for i in range(self.L):
            # Инициализация Ксавьера/Глорота
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            limit = np.sqrt(6 / (fan_in + fan_out))

            if activation == 'relu':
                # Инициализация He для ReLU
                std = np.sqrt(2.0 / fan_in)
                W = np.random.randn(fan_out, fan_in) * std
            else:
                # Инициализация Ксавьера для сигмоид/танх
                W = np.random.uniform(-limit, limit, (fan_out, fan_in))

            b = np.zeros((fan_out, 1))

            self.weights.append(W)
            self.biases.append(b)

    def activation_function(self, z: np.ndarray, derivative: bool = False) -> np.ndarray:
        """
        Функция активации

        Args:
            z: вход
            derivative: если True, возвращает производную
        """
        if self.activation == 'sigmoid':
            if derivative:
                sig = 1 / (1 + np.exp(-z))
                return sig * (1 - sig)
            return 1 / (1 + np.exp(-z))

        elif self.activation == 'relu':
            if derivative:
                return (z > 0).astype(float)
            return np.maximum(0, z)

        elif self.activation == 'tanh':
            if derivative:
                return 1 - np.tanh(z) ** 2
            return np.tanh(z)

        else:
            raise ValueError(f"Неизвестная функция активации: {self.activation}")

    def softmax(self, z: np.ndarray) -> np.ndarray:
        """
        Функция softmax для выходного слоя
        """
        exp_z = np.exp(z - np.max(z, axis=0, keepdims=True))
        return exp_z / np.sum(exp_z, axis=0, keepdims=True)

    def forward_propagation(self, X: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Прямое распространение

        Returns:
            A: активации каждого слоя
            Z: взвешенные суммы каждого слоя
        """
        A = [X]  # Активации (первый слой - вход)
        Z = []  # Взвешенные суммы

        # Прямое распространение через скрытые слои
        for l in range(self.L - 1):
            z = self.weights[l] @ A[l] + self.biases[l]
            a = self.activation_function(z)
            Z.append(z)
            A.append(a)

        # Выходной слой (softmax)
        z_out = self.weights[-1] @ A[-1] + self.biases[-1]
        a_out = self.softmax(z_out)
        Z.append(z_out)
        A.append(a_out)

        return A, Z

    def compute_loss(self, Y_pred: np.ndarray, Y_true: np.ndarray) -> float:
        """
        Вычисление функции потерь (кросс-энтропия + регуляризация L2)
        """
        m = Y_true.shape[1]

        # Перекрестная энтропия
        epsilon = 1e-15  # Для численной стабильности
        Y_pred = np.clip(Y_pred, epsilon, 1 - epsilon)
        cross_entropy = -np.sum(Y_true * np.log(Y_pred)) / m

        # Регуляризация L2
        reg_term = 0
        for W in self.weights:
            reg_term += np.sum(W ** 2)
        reg_term = (self.reg_lambda / (2 * m)) * reg_term

        return cross_entropy + reg_term

    def compute_accuracy(self, Y_pred: np.ndarray, Y_true: np.ndarray) -> float:
        """
        Вычисление точности
        """
        predictions = np.argmax(Y_pred, axis=0)
        labels = np.argmax(Y_true, axis=0)
        return np.mean(predictions == labels)

    def backward_propagation(self, X: np.ndarray, Y: np.ndarray,
                             A: List[np.ndarray], Z: List[np.ndarray]) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Обратное распространение ошибки

        Returns:
            dW: градиенты весов
            db: градиенты смещений
        """
        m = X.shape[1]
        dW = [None] * self.L
        db = [None] * self.L

        # Градиент для выходного слоя (softmax + cross-entropy)
        dZ = A[-1] - Y  # dL/dz для softmax+cross_entropy

        # Обратное распространение через слои
        for l in reversed(range(self.L)):
            if l == self.L - 1:
                # Для выходного слоя dZ уже вычислен
                pass
            else:
                # Для скрытых слоев
                dA = self.weights[l + 1].T @ dZ
                dZ = dA * self.activation_function(Z[l], derivative=True)

            # Градиенты весов и смещений с учетом регуляризации
            dW[l] = (dZ @ A[l].T) / m + (self.reg_lambda / m) * self.weights[l]
            db[l] = np.sum(dZ, axis=1, keepdims=True) / m

        return dW, db

    def update_parameters(self, dW: List[np.ndarray], db: List[np.ndarray]):
        """
        Обновление параметров с помощью градиентного спуска
        """
        for l in range(self.L):
            self.weights[l] -= self.learning_rate * dW[l]
            self.biases[l] -= self.learning_rate * db[l]

    def train(self, X_train: np.ndarray, Y_train: np.ndarray,
              X_val: np.ndarray, Y_val: np.ndarray,
              epochs: int = 50, batch_size: int = 32,
              verbose: bool = True) -> dict:
        """
        Обучение модели

        Returns:
            history: словарь с историей обучения
        """
        m = X_train.shape[1]
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }

        for epoch in range(epochs):
            # Перемешивание данных
            permutation = np.random.permutation(m)
            X_shuffled = X_train[:, permutation]
            Y_shuffled = Y_train[:, permutation]

            epoch_train_loss = 0
            epoch_train_acc = 0
            num_batches = 0

            # Мини-батчи
            for i in range(0, m, batch_size):
                X_batch = X_shuffled[:, i:i + batch_size]
                Y_batch = Y_shuffled[:, i:i + batch_size]

                # Прямое распространение
                A, Z = self.forward_propagation(X_batch)

                # Вычисление потерь и точности
                batch_loss = self.compute_loss(A[-1], Y_batch)
                batch_acc = self.compute_accuracy(A[-1], Y_batch)

                epoch_train_loss += batch_loss
                epoch_train_acc += batch_acc
                num_batches += 1

                # Обратное распространение
                dW, db = self.backward_propagation(X_batch, Y_batch, A, Z)

                # Обновление параметров
                self.update_parameters(dW, db)

            # Вычисление средних значений за эпоху
            avg_train_loss = epoch_train_loss / num_batches
            avg_train_acc = epoch_train_acc / num_batches

            # Валидация
            A_val, _ = self.forward_propagation(X_val)
            val_loss = self.compute_loss(A_val, Y_val)
            val_acc = self.compute_accuracy(A_val, Y_val)

            # Сохранение истории
            history['train_loss'].append(avg_train_loss)
            history['train_acc'].append(avg_train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)

            if verbose and (epoch % 5 == 0 or epoch == epochs - 1):
                print(f"Эпоха {epoch + 1}/{epochs}")
                print(f"  Потери: train={avg_train_loss:.4f}, val={val_loss:.4f}")
                print(f"  Точность: train={avg_train_acc * 100:.2f}%, val={val_acc * 100:.2f}%")

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Предсказание меток для входных данных
        """
        A, _ = self.forward_propagation(X)
        return np.argmax(A[-1], axis=0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Вероятности предсказаний
        """
        A, _ = self.forward_propagation(X)
        return A[-1]

    def save_model(self, filepath: str):
        """
        Сохранение модели
        """
        model_data = {
            'weights': self.weights,
            'biases': self.biases,
            'layer_sizes': self.layer_sizes,
            'activation': self.activation,
            'learning_rate': self.learning_rate,
            'reg_lambda': self.reg_lambda
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    @classmethod
    def load_model(cls, filepath: str):
        """
        Загрузка модели
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        model = cls(
            layer_sizes=model_data['layer_sizes'],
            learning_rate=model_data['learning_rate'],
            activation=model_data['activation'],
            reg_lambda=model_data['reg_lambda']
        )

        model.weights = model_data['weights']
        model.biases = model_data['biases']

        return model


def load_mnist(path: str = './data') -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Загрузка датасета MNIST
    """

    def load_images(filename):
        with gzip.open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=16)
        return data.reshape(-1, 784).T / 255.0  # Нормализация и транспонирование

    def load_labels(filename):
        with gzip.open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=8)
        return np.eye(10)[data].T  # One-hot encoding

    # Создание директории, если не существует
    os.makedirs(path, exist_ok=True)

    # Загрузка данных
    X_train = load_images(os.path.join(path, 'train-images-idx3-ubyte.gz'))
    Y_train = load_labels(os.path.join(path, 'train-labels-idx1-ubyte.gz'))
    X_test = load_images(os.path.join(path, 't10k-images-idx3-ubyte.gz'))
    Y_test = load_labels(os.path.join(path, 't10k-labels-idx1-ubyte.gz'))

    return X_train, Y_train, X_test, Y_test


def plot_training_history(history: dict, save_path: Optional[str] = None):
    """
    Построение графиков обучения
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # График потерь
    axes[0].plot(history['train_loss'], label='Train')
    axes[0].plot(history['val_loss'], label='Validation')
    axes[0].set_xlabel('Эпоха')
    axes[0].set_ylabel('Потери')
    axes[0].set_title('Функция потерь')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # График точности
    axes[1].plot(np.array(history['train_acc']) * 100, label='Train')
    axes[1].plot(np.array(history['val_acc']) * 100, label='Validation')
    axes[1].set_xlabel('Эпоха')
    axes[1].set_ylabel('Точность (%)')
    axes[1].set_title('Точность')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches='tight')

    plt.show()


def create_train_val_split(X_train: np.ndarray, Y_train: np.ndarray,
                           val_ratio: float = 0.2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Разделение тренировочных данных на train/validation
    """
    m = X_train.shape[1]
    val_size = int(m * val_ratio)

    indices = np.random.permutation(m)
    train_indices = indices[val_size:]
    val_indices = indices[:val_size]

    X_train_split = X_train[:, train_indices]
    Y_train_split = Y_train[:, train_indices]
    X_val = X_train[:, val_indices]
    Y_val = Y_train[:, val_indices]

    return X_train_split, Y_train_split, X_val, Y_val


def download_mnist():
    """
    Скачивание датасета MNIST, если его нет
    """
    import urllib.request

    base_url = 'http://yann.lecun.com/exdb/mnist/'
    files = [
        'train-images-idx3-ubyte.gz',
        'train-labels-idx1-ubyte.gz',
        't10k-images-idx3-ubyte.gz',
        't10k-labels-idx1-ubyte.gz'
    ]

    os.makedirs('./data', exist_ok=True)

    for file in files:
        filepath = f'./data/{file}'
        if not os.path.exists(filepath):
            print(f'Скачивание {file}...')
            urllib.request.urlretrieve(base_url + file, filepath)
            print(f'  Завершено!')
        else:
            print(f'{file} уже существует')