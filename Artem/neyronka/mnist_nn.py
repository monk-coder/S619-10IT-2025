## 💻 mnist_nn.py

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import time

# ----------------------------
# Вспомогательные функции
# ----------------------------

def sigmoid(z):
    # Устойчивая реализация сигмоиды
    return np.where(z >= 0,
                    1 / (1 + np.exp(-z)),
                    np.exp(z) / (1 + np.exp(z)))

def sigmoid_derivative(a):
    return a * (1 - a)

def softmax(z):
    # Устойчивая реализация softmax
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

def cross_entropy_loss(y_true, y_pred):
    m = y_true.shape[0]
    # Предотвращаем log(0)
    y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
    return -np.sum(y_true * np.log(y_pred)) / m

def one_hot_encode(y, num_classes=10):
    return np.eye(num_classes)[y]

# ----------------------------
# Класс нейросети
# ----------------------------

class SimpleNeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        # Инициализация весов (Xavier-like)
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))

    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = sigmoid(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = softmax(self.z2)
        return self.a2

    def backward(self, X, y_true, y_pred):
        m = X.shape[0]

        # Градиенты на выходном слое
        dz2 = y_pred - y_true  # для softmax + cross-entropy
        dW2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m

        # Градиенты на скрытом слое
        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * sigmoid_derivative(self.a1)
        dW1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m

        # Обновление весов
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1

    def train(self, X_train, y_train, X_val, y_val, epochs=20):
        train_losses = []
        val_accuracies = []

        for epoch in range(epochs):
            # Forward pass
            y_pred = self.forward(X_train)
            loss = cross_entropy_loss(y_train, y_pred)
            train_losses.append(loss)

            # Backward pass
            self.backward(X_train, y_train, y_pred)

            # Validation accuracy
            val_pred = self.forward(X_val)
            val_acc = np.mean(np.argmax(val_pred, axis=1) == np.argmax(y_val, axis=1))
            val_accuracies.append(val_acc)

            if epoch % 5 == 0 or epoch == epochs - 1:
                print(f"Epoch {epoch}, Loss: {loss:.4f}, Val Acc: {val_acc:.4f}")

        return train_losses, val_accuracies

    def predict(self, X):
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

# ----------------------------
# Основной скрипт
# ----------------------------

def main():
    print("Загрузка данных MNIST...")
    X, y = fetch_openml('mnist_784', version=1, return_X_y=True, as_frame=False, parser='liac-arff')
    X = X.astype('float32')
    y = y.astype('int')

    # Нормализация
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Разделение
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )

    # One-hot encoding
    y_train_oh = one_hot_encode(y_train)
    y_val_oh = one_hot_encode(y_val)
    y_test_oh = one_hot_encode(y_test)

    print(f"Train size: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

    # Создание модели
    model = SimpleNeuralNetwork(
        input_size=784,
        hidden_size=128,
        output_size=10,
        learning_rate=0.1
    )

    # Обучение
    print("\nНачало обучения...")
    start_time = time.time()
    losses, accuracies = model.train(X_train, y_train_oh, X_val, y_val_oh, epochs=30)
    print(f"Обучение завершено за {time.time() - start_time:.2f} секунд")

    # Оценка на тесте
    test_pred = model.predict(X_test)
    test_acc = np.mean(test_pred == y_test)
    print(f"\nТочность на тестовой выборке: {test_acc:.4f} ({test_acc * 100:.2f}%)")

    # Графики
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(losses, label='Training Loss')
    plt.title('Loss по эпохам')
    plt.xlabel('Эпоха')
    plt.ylabel('Loss')
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(accuracies, label='Validation Accuracy', color='orange')
    plt.title('Точность на валидации')
    plt.xlabel('Эпоха')
    plt.ylabel('Accuracy')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('training_plots.png')
    plt.show()

    # Проверка: если точность < 60%, предупреждение
    if test_acc < 0.6:
        print("\n⚠️  ВНИМАНИЕ: Точность ниже 60%! Проверьте гиперпараметры.")
    else:
        print("\n✅ Точность выше 60% — работа готова к защите.")

if __name__ == "__main__":
    main()