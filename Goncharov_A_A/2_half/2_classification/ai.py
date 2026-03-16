import gzip
import os
import urllib.request
from urllib.error import HTTPError, URLError
import matplotlib.pyplot as plt
import numpy as np


INPUT_SIZE = 784
HIDDEN_SIZE = 128
OUTPUT_SIZE = 10
LEARNING_RATE = 0.01
BATCH_SIZE = 128
EPOCHS = 50
DATA_DIR = "data"
GRAPH_FILENAME = "training_history.png"


def one_hot(y, num_classes=10):
    result = np.zeros((y.size, num_classes))
    result[np.arange(y.size), y] = 1
    return result


def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


class NeuralNetwork:
    def __init__(self, input_size=784, hidden_size=128, output_size=10, lr=0.01):
        self.lr = lr
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
        X_batch = X_shuffled[i : i + batch_size]
        y_batch = y_shuffled[i : i + batch_size]
        batches.append((X_batch, y_batch))

    return batches


def _download(url: str, dst_path: str, timeout: int = 30) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if os.path.exists(dst_path):
        return

    print(f"downloading: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (MNIST-downloader for school project)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()

    if len(data) < 1024:
        raise RuntimeError(
            f"response too small when downloading (len={len(data)}). possibly blocked/proxy: {url}"
        )

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
        shape.append(int.from_bytes(data[idx : idx + 4], "big"))
        idx += 4

    if dtype_code != 0x08:
        raise ValueError(f"unexpected dtype_code={dtype_code} in idx file: {path}")

    arr = np.frombuffer(data, dtype=np.uint8, offset=idx)
    return arr.reshape(shape)


def load_mnist(data_dir: str = DATA_DIR):
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
    for base in MNIST_URLS:  # noqa: F821
        try:
            for k, fname in files.items():
                _download(f"{base}/{fname}", paths[k])
            last_err = None
            break
        except (URLError, HTTPError, TimeoutError, OSError, RuntimeError) as e:
            last_err = e
            print(f"failed to download from mirror: {base} ({type(e).__name__}: {e})")
            continue

    if last_err is not None:
        error_message = "erore"
        raise RuntimeError(error_message) from last_err

    X_train = _read_idx_gz(paths["train_images"])
    y_train = _read_idx_gz(paths["train_labels"])
    X_test = _read_idx_gz(paths["test_images"])
    y_test = _read_idx_gz(paths["test_labels"])

    return (X_train, y_train), (X_test, y_test)


def train_and_evaluate():
    print("loading mnist dataset")
    (X_train, y_train), (X_test, y_test) = load_mnist(data_dir=DATA_DIR)

    X_train = X_train.reshape(X_train.shape[0], -1)
    X_test = X_test.reshape(X_test.shape[0], -1)

    X_train = X_train.astype(np.float32) / 255.0
    X_test = X_test.astype(np.float32) / 255.0

    y_train_oh = one_hot(y_train)
    y_test_oh = one_hot(y_test)

    print(
        f"trainin samplies: {X_train.shape[0]:,}, testing saplies: {X_test.shape[0]:,}"
    )

    nn = NeuralNetwork(
        input_size=INPUT_SIZE,
        hidden_size=HIDDEN_SIZE,
        output_size=OUTPUT_SIZE,
        lr=LEARNING_RATE,
    )

    print(f"ai done with {INPUT_SIZE} -> {HIDDEN_SIZE} -> {OUTPUT_SIZE} neurons")

    loss_history = []
    acc_history = []
    test_loss_history = []
    test_acc_history = []

    print("starting training...")
    for epoch in range(EPOCHS):
        batches = create_batches(X_train, y_train_oh, BATCH_SIZE)
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
            print(
                f"epoha {epoch + 1:3d}/{EPOCHS}, train poterya: {avg_loss:.4f}, akuratnost': {train_acc:.4f}, test akuratnost: {test_acc:.4f}"
            )

    final_test_acc = accuracy(y_test, np.argmax(nn.forward(X_test), axis=1))
    final_test_loss = nn.loss(nn.forward(X_test), y_test_oh)

    print(f"final test akuratnost: {final_test_acc:.4f} ({final_test_acc * 100:.2f}%)")
    print(f"final test poterya: {final_test_loss:.4f}")

    print("plotting training graphs")
    plot_training_graphs(loss_history, acc_history, test_loss_history, test_acc_history)
    print("training completed")


def plot_training_graphs(
    loss_history, acc_history, test_loss_history, test_acc_history
):
    plt.figure(figsize=(14, 5))

    plt.subplot(1, 2, 1)
    plt.plot(loss_history, label="train loss", color="blue")
    plt.plot(test_loss_history, label="test loss", color="red")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.title("loss function per epoch")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(acc_history, label="train accuracy", color="blue")
    plt.plot(test_acc_history, label="test accuracy", color="red")
    plt.xlabel("epoch")
    plt.ylabel("accuracy")
    plt.title("accuracy per epoch")
    plt.legend()

    plt.tight_layout()
    plt.savefig(GRAPH_FILENAME)
    print(f"\ngraphs saved in '{GRAPH_FILENAME}'")
    plt.close() 


if __name__ == "__main__":
    train_and_evaluate()
