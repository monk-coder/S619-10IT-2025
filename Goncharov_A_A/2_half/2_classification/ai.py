import os
import gzip
import urllib.request
from urllib.error import URLError, HTTPError

if "MPLCONFIGDIR" not in os.environ:
    _mpl_dir = os.path.join(os.path.dirname(__file__), ".mplconfig")
    os.makedirs(_mpl_dir, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = _mpl_dir

import numpy as np
import matplotlib.pyplot as plt


def one_hot(y, num_classes=10):
    result = np.zeros((y.size, num_classes))
    result[np.arange(y.size), y] = 1
    return result


def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


class NeuralNetwork:
    def __init__(self, input_size=784, hidden_size=128, output_size=10, lr=0.01):
        self.lr = lr
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(1.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))
    
    def relu(self, z):
        return np.maximum(0, z)
    
    def relu_derivative(self, z):
        return (z > 0).astype(float)
    
    def softmax(self, z):
        exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)
    
    def forward(self, X):
        self.Z1 = X @ self.W1 + self.b1
        self.A1 = self.relu(self.Z1)
        
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = self.softmax(self.Z2)
        
        return self.A2
    
    def loss(self, y_pred, y_true):
        epsilon = 1e-9
        return -np.mean(np.sum(y_true * np.log(y_pred + epsilon), axis=1))
    
    def backward(self, X, y_true):
        m = X.shape[0]
        dZ2 = self.A2 - y_true
        dW2 = (self.A1.T @ dZ2) / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * self.relu_derivative(self.Z1)
        dW1 = (X.T @ dZ1) / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1


def create_batches(X, y, batch_size):
    batches = []
    n_samples = X.shape[0]
    indices = np.random.permutation(n_samples)
    X_shuffled = X[indices]
    y_shuffled = y[indices]
    for i in range(0, n_samples, batch_size):
        X_batch = X_shuffled[i:i + batch_size]
        y_batch = y_shuffled[i:i + batch_size]
        batches.append((X_batch, y_batch))
    
    return batches


MNIST_URLS = [
    "https://storage.googleapis.com/cvdf-datasets/mnist",
    "https://ossci-datasets.s3.amazonaws.com/mnist",
    "http://yann.lecun.com/exdb/mnist",
    "https://yann.lecun.com/exdb/mnist",
]


def _download(url: str, dst_path: str, timeout: int = 30) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if os.path.exists(dst_path):
        return

    print(f"Скачивание: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (MNIST-downloader for school project)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()

    if len(data) < 1024:
        raise RuntimeError(f"Слишком маленький ответ при скачивании (len={len(data)}). Возможно, блокировка/прокси: {url}")

    with open(dst_path, "wb") as f:
        f.write(data)


def _read_idx_gz(path: str) -> np.ndarray:
    with gzip.open(path, "rb") as f:
        data = f.read()

    dtype_code = data[2]
    dims = data[3]

    shape = []
    idx = 4
    for _ in range(dims):
        shape.append(int.from_bytes(data[idx:idx + 4], "big"))
        idx += 4

    if dtype_code != 0x08:
        raise ValueError(f"Неожиданный dtype_code={dtype_code} в IDX файле: {path}")

    arr = np.frombuffer(data, dtype=np.uint8, offset=idx)
    return arr.reshape(shape)


def load_mnist(data_dir: str = "data"):
    files = {
        "train_images": "train-images-idx3-ubyte.gz",
        "train_labels": "train-labels-idx1-ubyte.gz",
        "test_images": "t10k-images-idx3-ubyte.gz",
        "test_labels": "t10k-labels-idx1-ubyte.gz",
    }

    paths = {k: os.path.join(data_dir, v) for k, v in files.items()}

    if all(os.path.exists(p) for p in paths.values()):
        X_train = _read_idx_gz(paths["train_images"])
        y_train = _read_idx_gz(paths["train_labels"])
        X_test = _read_idx_gz(paths["test_images"])
        y_test = _read_idx_gz(paths["test_labels"])
        return (X_train, y_train), (X_test, y_test)

    last_err = None
    for base in MNIST_URLS:
        try:
            for k, fname in files.items():
                _download(f"{base}/{fname}", paths[k])
            last_err = None
            break
        except (URLError, HTTPError, TimeoutError, OSError, RuntimeError) as e:
            last_err = e
            print(f"Не удалось скачать с зеркала: {base} ({type(e).__name__}: {e})")
            continue

    if last_err is not None:
        raise RuntimeError(
            "Не удалось скачать MNIST.\n"
            "Возможные причины:\n"
            "- нет доступа в интернет / школьный прокси\n"
            "- DNS не работает (часто ошибка вида 'Errno 8 nodename nor servname provided')\n"
            "- требуется вход через captive-portal в Wi‑Fi\n"
            "- блокировка доменов/HTTPS\n\n"
            "Что делать:\n"
            "1) Попробуйте другой интернет (например, раздать с телефона) и запустите ещё раз.\n"
            "2) Или скачайте 4 файла MNIST вручную и положите в папку 'data/' рядом с ai.py:\n"
            "   - train-images-idx3-ubyte.gz\n"
            "   - train-labels-idx1-ubyte.gz\n"
            "   - t10k-images-idx3-ubyte.gz\n"
            "   - t10k-labels-idx1-ubyte.gz\n\n"
            f"Техническая ошибка последней попытки: {type(last_err).__name__}: {last_err}"
        ) from last_err

    X_train = _read_idx_gz(paths["train_images"])
    y_train = _read_idx_gz(paths["train_labels"])
    X_test = _read_idx_gz(paths["test_images"])
    y_test = _read_idx_gz(paths["test_labels"])

    return (X_train, y_train), (X_test, y_test)


print("=" * 70)
print("ЗАГРУЗКА ДАТАСЕТА MNIST")
print("=" * 70)
(X_train, y_train), (X_test, y_test) = load_mnist(data_dir="data")

X_train = X_train.reshape(X_train.shape[0], -1)
X_test = X_test.reshape(X_test.shape[0], -1)

X_train = X_train.astype(np.float32) / 255.0
X_test = X_test.astype(np.float32) / 255.0

y_train_oh = one_hot(y_train)
y_test_oh = one_hot(y_test)

print(f"Размер обучающей выборки: {X_train.shape[0]:,}")
print(f"Размер тестовой выборки: {X_test.shape[0]:,}")
print(f"Размерность входных данных: {X_train.shape[1]}")

print("\n" + "=" * 70)
print("СОЗДАНИЕ И ОБУЧЕНИЕ МОДЕЛИ")
print("=" * 70)

input_size = 784
hidden_size = 128
output_size = 10
learning_rate = 0.01
batch_size = 128
epochs = 50

nn = NeuralNetwork(
    input_size=input_size,
    hidden_size=hidden_size,
    output_size=output_size,
    lr=learning_rate
)

print(f"\nАрхитектура сети:")
print(f"  - Входной слой: {input_size} нейронов")
print(f"  - Скрытый слой: {hidden_size} нейронов (ReLU)")
print(f"  - Выходной слой: {output_size} нейронов (Softmax)")
print(f"\nПараметры обучения:")
print(f"  - Learning rate: {learning_rate}")
print(f"  - Batch size: {batch_size}")
print(f"  - Epochs: {epochs}")

loss_history = []
acc_history = []
test_loss_history = []
test_acc_history = []

print("\n" + "-" * 70)
print("НАЧАЛО ОБУЧЕНИЯ")
print("-" * 70)

for epoch in range(epochs):
    batches = create_batches(X_train, y_train_oh, batch_size)
    epoch_loss = 0
    
    for X_batch, y_batch in batches:
        y_pred = nn.forward(X_batch)
        
        batch_loss = nn.loss(y_pred, y_batch)
        epoch_loss += batch_loss
        
        nn.backward(X_batch, y_batch)
    
    avg_loss = epoch_loss / len(batches)
    
    train_pred = nn.forward(X_train)
    train_acc = accuracy(y_train, np.argmax(train_pred, axis=1))
    
    test_pred = nn.forward(X_test)
    test_loss = nn.loss(test_pred, y_test_oh)
    test_acc = accuracy(y_test, np.argmax(test_pred, axis=1))
    
    loss_history.append(avg_loss)
    acc_history.append(train_acc)
    test_loss_history.append(test_loss)
    test_acc_history.append(test_acc)
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"Epoch {epoch+1:3d}/{epochs} | "
              f"Train Loss: {avg_loss:.4f} | Train Acc: {train_acc:.4f} | "
              f"Test Loss: {test_loss:.4f} | Test Acc: {test_acc:.4f}")

print("-" * 70)

print("\n" + "=" * 70)
print("ФИНАЛЬНАЯ ОЦЕНКА МОДЕЛИ")
print("=" * 70)

final_test_pred = nn.forward(X_test)
final_test_acc = accuracy(y_test, np.argmax(final_test_pred, axis=1))
final_test_loss = nn.loss(final_test_pred, y_test_oh)

print(f"\nФинальная точность на тестовой выборке: {final_test_acc:.4f} ({final_test_acc*100:.2f}%)")
print(f"Финальная функция потерь на тестовой выборке: {final_test_loss:.4f}")

if final_test_acc >= 0.60:
    print("\n✓ Модель достигла требуемой точности (≥60%)")
else:
    print("\n⚠ Модель не достигла требуемой точности (≥60%)")

print("\n" + "=" * 70)
print("ПОСТРОЕНИЕ ГРАФИКОВ ОБУЧЕНИЯ")
print("=" * 70)

plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.plot(loss_history, label='Train Loss', linewidth=2, color='blue')
plt.plot(test_loss_history, label='Test Loss', linewidth=2, color='red')
plt.xlabel('Эпоха', fontsize=12)
plt.ylabel('Loss', fontsize=12)
plt.title('Функция потерь на каждой эпохе', fontsize=14, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(acc_history, label='Train Accuracy', linewidth=2, color='blue')
plt.plot(test_acc_history, label='Test Accuracy', linewidth=2, color='red')
plt.xlabel('Эпоха', fontsize=12)
plt.ylabel('Accuracy', fontsize=12)
plt.title('Точность на каждой эпохе', fontsize=14, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('training_history.png', dpi=150, bbox_inches='tight')
print("\nГрафики сохранены в файл 'training_history.png'")
plt.show()

print("\n" + "=" * 70)
print("ОБУЧЕНИЕ ЗАВЕРШЕНО")
print("=" * 70)
