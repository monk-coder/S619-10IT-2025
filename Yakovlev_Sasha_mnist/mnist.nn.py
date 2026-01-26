import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
import os

# Создаём папку для графиков, если её нет
os.makedirs("plots", exist_ok=True)

# ----------------------------
# Вспомогательные функции
# ----------------------------

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

def one_hot_encode(y, num_classes=10):
    return np.eye(num_classes)[y]

def initialize_weights_xavier(input_size, output_size):
    """Инициализация весов по методу Xavier (Glorot)."""
    scale = np.sqrt(2.0 / (input_size + output_size))
    return np.random.randn(input_size, output_size) * scale

def initialize_bias(output_size):
    """Инициализация смещений нулями."""
    return np.zeros((1, output_size))

# ----------------------------
# Класс нейронной сети
# ----------------------------

class SimpleNeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        # Инициализация параметров
        self.W1 = initialize_weights_xavier(input_size, hidden_size)
        self.b1 = initialize_bias(hidden_size)
        self.W2 = initialize_weights_xavier(hidden_size, output_size)
        self.b2 = initialize_bias(output_size)

    def _layer1(self, X):
        """Первый скрытый слой: линейное преобразование + сигмоида."""
        z1 = np.dot(X, self.W1) + self.b1
        return sigmoid(z1)

    def _layer2(self, a1):
        """Выходной слой: линейное преобразование + softmax."""
        z2 = np.dot(a1, self.W2) + self.b2
        return softmax(z2)

    def forward(self, X):
        """Прямое распространение через два слоя."""
        self.a1 = self._layer1(X)
        self.a2 = self._layer2(self.a1)
        return self.a2

    def backward(self, X, y_true, y_pred):
        m = X.shape[0]

        # Градиенты для выходного слоя
        dz2 = y_pred - y_true
        dW2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m

        # Градиенты для скрытого слоя
        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * sigmoid_derivative(np.dot(X, self.W1) + self.b1)
        dW1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m

        # Обновление весов
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1

    def train(self, X_train, y_train, X_val, y_val, epochs=50):
        train_losses = []
        val_accuracies = []

        for epoch in range(epochs):
            y_pred = self.forward(X_train)
            loss = cross_entropy_loss(y_train, y_pred)
            train_losses.append(loss)

            self.backward(X_train, y_train, y_pred)

            val_pred = self.forward(X_val)
            val_acc = self.accuracy(val_pred, y_val)
            val_accuracies.append(val_acc)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {loss:.4f}, Val Acc: {val_acc:.4f}")

        return train_losses, val_accuracies

    def predict(self, X):
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

    def accuracy(self, y_pred, y_true):
        if y_true.ndim == 2:
            y_true = np.argmax(y_true, axis=1)
        y_pred_labels = np.argmax(y_pred, axis=1)
        return np.mean(y_pred_labels == y_true)

# ----------------------------
# Основная программа
# ----------------------------

def main():
    print("Загрузка данных MNIST...")
    mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
    X = mnist.data.astype(np.float64)
    y = mnist.target.astype(int)

    # Нормализация
    X = X / 255.0

    # Разделение данных
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=10000, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=5000, random_state=42, stratify=y_train
    )

    # One-hot encoding
    y_train_oh = one_hot_encode(y_train)
    y_val_oh = one_hot_encode(y_val)

    print(f"Размеры: train={X_train.shape[0]}, val={X_val.shape[0]}, test={X_test.shape[0]}")

    # Создание и обучение модели
    model = SimpleNeuralNetwork(
        input_size=784,
        hidden_size=128,
        output_size=10,
        learning_rate=0.1
    )

    print("\nНачало обучения...")
    losses, accuracies = model.train(X_train, y_train_oh, X_val, y_val_oh, epochs=50)

    # Финальная оценка
    test_pred = model.predict(X_test)
    test_acc = np.mean(test_pred == y_test)
    print(f"\nФинальная точность на тестовой выборке: {test_acc:.4f} ({test_acc*100:.2f}%)")

    # Построение графиков
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(losses, label='Training Loss')
    plt.title('Функция потерь')
    plt.xlabel('Эпоха')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(accuracies, label='Validation Accuracy', color='orange')
    plt.title('Точность на валидации')
    plt.xlabel('Эпоха')
    plt.ylabel('Accuracy')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig("plots/training_curves.png")
    plt.show()

if __name__ == "__main__":
    main()
