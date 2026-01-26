import numpy as np
import matplotlib.pyplot as plt
import os

# === НАСТРОЙКА ===
DATASET_MODE = "digits"  #  "letters" or "digits"

os.makedirs("plots", exist_ok=True)


def sigmoid(z):
    z = np.clip(z, -500, 500)
    return 1 / (1 + np.exp(-z))


def sigmoid_derivative(z):
    s = sigmoid(z)
    return s * (1 - s)


def softmax(z):
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)


def cross_entropy_loss(y_true, y_pred):
    m = y_true.shape[0]
    y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
    return -np.sum(y_true * np.log(y_pred)) / m


def one_hot_encode(y, num_classes):
    return np.eye(num_classes)[y]


def initialize_weights_xavier(input_size, output_size):
    scale = np.sqrt(2.0 / (input_size + output_size))
    return np.random.randn(input_size, output_size) * scale


def initialize_bias(output_size):
    return np.zeros((1, output_size))


class SimpleNeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.W1 = initialize_weights_xavier(input_size, hidden_size)
        self.b1 = initialize_bias(hidden_size)
        self.W2 = initialize_weights_xavier(hidden_size, output_size)
        self.b2 = initialize_bias(output_size)
        self.learning_rate = learning_rate

    def _layer1(self, X):
        return sigmoid(np.dot(X, self.W1) + self.b1)

    def _layer2(self, a1):
        return softmax(np.dot(a1, self.W2) + self.b2)

    def forward(self, X):
        self.a1 = self._layer1(X)
        self.a2 = self._layer2(self.a1)
        return self.a2

    def backward(self, X, y_true, y_pred):
        m = X.shape[0]
        dz2 = y_pred - y_true
        dW2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m

        da1 = np.dot(dz2, self.W2.T)
        z1 = np.dot(X, self.W1) + self.b1
        dz1 = da1 * sigmoid_derivative(z1)
        dW1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m

        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2

    def train(self, X_train, y_train, X_val, y_val, epochs=50):
        losses, accs = [], []
        for epoch in range(epochs):
            y_pred = self.forward(X_train)
            loss = cross_entropy_loss(y_train, y_pred)
            losses.append(loss)
            self.backward(X_train, y_train, y_pred)

            val_acc = self.accuracy(self.forward(X_val), y_val)
            accs.append(val_acc)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}, Val Acc: {val_acc:.4f}")
        return losses, accs

    def predict(self, X):
        return np.argmax(self.forward(X), axis=1)

    def accuracy(self, y_pred, y_true):
        if y_true.ndim == 2:
            y_true = np.argmax(y_true, axis=1)
        return np.mean(np.argmax(y_pred, axis=1) == y_true)


def load_dataset(mode):
    if mode == "digits":
        print("Загрузка MNIST (цифры 0–9) через интернет...")
        from sklearn.datasets import fetch_openml
        mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
        X = mnist.data.astype(np.float64)
        y = mnist.target.astype(int)
        num_classes = 10
        class_names = "0–9"
    elif mode == "letters":
        print("Загрузка EMNIST Letters из файла emnist-letters.mat...")
        mat_path = "emnist-letters.mat"
        if not os.path.exists(mat_path):
            raise FileNotFoundError(
                f"Файл '{mat_path}' не найден. Скачайте его с:\n"
                "https://www.itl.nist.gov/iaui/vip/cs_links/EMNIST/matlab.zip\n"
                "и поместите в эту папку."
            )
        import scipy.io
        mat = scipy.io.loadmat(mat_path)
        X = mat['dataset'][0][0][0][0][0][0].astype(np.float64)
        y = mat['dataset'][0][0][0][0][0][1].flatten().astype(int)
        y = y - 1  # 1–26 → 0–25
        X = X.reshape(-1, 28, 28)
        X = np.transpose(X, (0, 2, 1))
        X = X.reshape(-1, 784)
        num_classes = 26
        class_names = "A–Z"
    else:
        raise ValueError("DATASET_MODE должен быть 'digits' или 'letters'")

    X = X / 255.0
    return X, y, num_classes, class_names


def main():
    X, y, num_classes, class_names = load_dataset(DATASET_MODE)

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=10000, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=5000, random_state=42, stratify=y_train
    )

    y_train_oh = one_hot_encode(y_train, num_classes)
    y_val_oh = one_hot_encode(y_val, num_classes)

    print(f"Режим: {DATASET_MODE} ({class_names}) | Классов: {num_classes}")

    model = SimpleNeuralNetwork(28*28, 2**7, num_classes, learning_rate=0.1)
    losses, accuracies = model.train(X_train, y_train_oh, X_val, y_val_oh, epochs=50)

    test_acc = model.accuracy(model.forward(X_test), y_test)
    print(f"\n✅ Точность на тесте ({class_names}): {test_acc:.4f} ({test_acc * 100:.2f}%)")

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(losses)
    plt.title(f'Loss ({class_names})')
    plt.xlabel('Эпоха')
    plt.ylabel('Loss')
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(accuracies, color='orange')
    plt.title(f'Accuracy ({class_names})')
    plt.xlabel('Эпоха')
    plt.ylabel('Accuracy')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(f"plots/training_curves_{DATASET_MODE}.png")
    plt.show()


if __name__ == "__main__":
    main()
