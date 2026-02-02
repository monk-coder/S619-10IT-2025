#!/usr/bin/env python3
"""
Основной файл для запуска нейронной сети MNIST
ВСЕ КОМПОНЕНТЫ В ОДНОМ ФАЙЛЕ
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from tqdm import tqdm
import sys
import os


# ==================== 1. КЛАССЫ АКТИВАЦИИ ====================
class ReLU:
    def __init__(self):
        self.mask = None

    def forward(self, x):
        self.mask = (x <= 0)
        out = x.copy()
        out[self.mask] = 0
        return out

    def backward(self, dout):
        dout[self.mask] = 0
        return dout


class Softmax:
    def __init__(self):
        self.out = None

    def forward(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        self.out = exp_x / np.sum(exp_x, axis=1, keepdims=True)
        return self.out

    def backward(self, dout):
        return dout


# ==================== 2. СЛОИ НЕЙРОННОЙ СЕТИ ====================
class DenseLayer:
    def __init__(self, input_size, output_size, activation=None):
        # Инициализация весов методом Xavier/Glorot
        limit = np.sqrt(6 / (input_size + output_size))
        self.weights = np.random.uniform(-limit, limit, (input_size, output_size))
        self.biases = np.zeros((1, output_size))
        self.activation = activation
        self.input = None
        self.z = None  # Взвешенная сумма перед активацией
        self.output = None
        self.dweights = None
        self.dbiases = None

    def forward(self, x):
        """Прямое распространение"""
        self.input = x
        self.z = np.dot(x, self.weights) + self.biases

        if self.activation:
            self.output = self.activation.forward(self.z)
        else:
            self.output = self.z

        return self.output

    def backward(self, dout):
        """Обратное распространение"""
        batch_size = dout.shape[0]

        # Если есть функция активации, применяем ее обратное распространение
        if self.activation:
            dout = self.activation.backward(dout)

        # Градиенты весов и смещений
        self.dweights = np.dot(self.input.T, dout) / batch_size
        self.dbiases = np.sum(dout, axis=0, keepdims=True) / batch_size

        # Градиент для предыдущего слоя
        return np.dot(dout, self.weights.T)

    def update_parameters(self, learning_rate):
        """Обновление параметров"""
        self.weights -= learning_rate * self.dweights
        self.biases -= learning_rate * self.dbiases


# ==================== 3. ФУНКЦИЯ ПОТЕРЬ ====================
class CrossEntropyLoss:
    def __init__(self):
        self.y_pred = None
        self.y_true = None
        self.batch_size = None

    def forward(self, y_pred, y_true):
        """Вычисление кросс-энтропии"""
        self.batch_size = y_pred.shape[0]
        self.y_pred = y_pred
        self.y_true = y_true

        # Добавляем малую константу для избежания log(0)
        y_pred_clipped = np.clip(y_pred, 1e-7, 1 - 1e-7)

        # Вычисляем кросс-энтропию
        correct_logprobs = -np.log(y_pred_clipped) * y_true
        loss = np.sum(correct_logprobs) / self.batch_size
        return loss

    def backward(self):
        """Градиент для softmax + cross_entropy"""
        dx = self.y_pred - self.y_true
        dx = dx / self.batch_size
        return dx


# ==================== 4. ОПТИМИЗАТОР ====================
class SGD:
    """Стохастический градиентный спуск с моментумом"""

    def __init__(self, learning_rate=0.01, momentum=0.9):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.velocity = {}

    def update(self, layer, layer_id):
        """Обновление параметров слоя с моментумом"""
        if layer_id not in self.velocity:
            self.velocity[layer_id] = {
                'weights': np.zeros_like(layer.weights),
                'biases': np.zeros_like(layer.biases)
            }

        # Обновление скорости с моментумом
        self.velocity[layer_id]['weights'] = (
                self.momentum * self.velocity[layer_id]['weights'] -
                self.learning_rate * layer.dweights
        )
        self.velocity[layer_id]['biases'] = (
                self.momentum * self.velocity[layer_id]['biases'] -
                self.learning_rate * layer.dbiases
        )

        # Обновление параметров
        layer.weights += self.velocity[layer_id]['weights']
        layer.biases += self.velocity[layer_id]['biases']


# ==================== 5. НЕЙРОННАЯ СЕТЬ ====================
class NeuralNetwork:
    """Нейронная сеть для классификации"""

    def __init__(self, input_size, hidden_size, output_size):
        """
        input_size: размер входных данных (для MNIST: 784)
        hidden_size: количество нейронов в скрытом слое
        output_size: количество классов (для MNIST: 10)
        """
        self.layers = []
        self.loss_function = CrossEntropyLoss()
        self.optimizer = None

        # Создание слоев
        self.layers.append(DenseLayer(input_size, hidden_size, ReLU()))
        self.layers.append(DenseLayer(hidden_size, output_size, Softmax()))

    def set_optimizer(self, optimizer):
        """Установка оптимизатора"""
        self.optimizer = optimizer

    def forward(self, X):
        """Прямое распространение через все слои"""
        output = X
        for layer in self.layers:
            output = layer.forward(output)
        return output

    def backward(self, dout):
        """Обратное распространение через все слои"""
        grad = dout
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

    def compute_loss(self, y_pred, y_true):
        """Вычисление функции потерь"""
        return self.loss_function.forward(y_pred, y_true)

    def train_step(self, X_batch, y_batch, learning_rate):
        """Один шаг обучения на батче"""
        # Прямое распространение
        y_pred = self.forward(X_batch)

        # Вычисление потерь
        loss = self.compute_loss(y_pred, y_batch)

        # Обратное распространение
        dout = self.loss_function.backward()
        self.backward(dout)

        # Обновление параметров
        if self.optimizer:
            for i, layer in enumerate(self.layers):
                if layer.dweights is not None:
                    self.optimizer.update(layer, i)
        else:
            # Простое обновление градиентным спуском
            for layer in self.layers:
                if layer.dweights is not None:
                    layer.update_parameters(learning_rate)

        return loss, y_pred

    def predict(self, X):
        """Предсказание для новых данных"""
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

    def evaluate(self, X, y):
        """Оценка точности на данных"""
        y_pred = self.forward(X)
        predictions = np.argmax(y_pred, axis=1)
        labels = np.argmax(y, axis=1)
        return np.mean(predictions == labels)


# ==================== 6. УТИЛИТЫ ====================
def load_mnist_data():
    """Загрузка и подготовка данных MNIST"""
    print("Загрузка данных MNIST...")

    try:
        # Способ 1: Без pandas
        mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='liac-arff')
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        print("Пробуем альтернативный способ...")

        # Способ 2: Скачиваем с помощью sklearn
        from sklearn.datasets import load_digits
        digits = load_digits()
        X = digits.data.astype('float32')
        y = digits.target.astype('int')

        # Нормализация
        X = X / 16.0  # Для digits значения от 0 до 16

        # Преобразование меток в one-hot encoding
        lb = LabelBinarizer()
        y_onehot = lb.fit_transform(y)

        # Разделение на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_onehot, test_size=0.2, random_state=42
        )

        print(f"Размер обучающей выборки: {X_train.shape}")
        print(f"Размер тестовой выборки: {X_test.shape}")

        return X_train, X_test, y_train, y_test, lb

    X = mnist.data.astype('float32')
    y = mnist.target.astype('int')

    # Нормализация пикселей в диапазон [0, 1]
    X = X / 255.0

    # Преобразование меток в one-hot encoding
    lb = LabelBinarizer()
    y_onehot = lb.fit_transform(y)

    # Разделение на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_onehot, test_size=0.2, random_state=42
    )

    print(f"Размер обучающей выборки: {X_train.shape}")
    print(f"Размер тестовой выборки: {X_test.shape}")

    return X_train, X_test, y_train, y_test, lb


def create_minibatches(X, y, batch_size=32, shuffle=True):
    """Создание мини-батчей"""
    n_samples = X.shape[0]

    if shuffle:
        indices = np.random.permutation(n_samples)
        X = X[indices]
        y = y[indices]

    for i in range(0, n_samples, batch_size):
        yield (
            X[i:i + batch_size],
            y[i:i + batch_size]
        )


def accuracy(y_pred, y_true):
    """Вычисление точности классификации"""
    predictions = np.argmax(y_pred, axis=1)
    labels = np.argmax(y_true, axis=1)
    return np.mean(predictions == labels)


def plot_training_history(history):
    """Построение графиков обучения"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # График функции потерь
    ax1.plot(history['loss'], label='Обучающая выборка', marker='o')
    ax1.plot(history['val_loss'], label='Валидационная выборка', marker='s')
    ax1.set_xlabel('Эпоха')
    ax1.set_ylabel('Потери')
    ax1.set_title('Функция потерь')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # График точности
    ax2.plot(history['accuracy'], label='Обучающая выборка', marker='o')
    ax2.plot(history['val_accuracy'], label='Валидационная выборка', marker='s')
    ax2.set_xlabel('Эпоха')
    ax2.set_ylabel('Точность')
    ax2.set_title('Точность классификации')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('training_history.png', dpi=100)
    plt.show()


# ==================== 7. ОБУЧЕНИЕ МОДЕЛИ ====================
def train_model(model, X_train, y_train, X_val, y_val,
                epochs=10, batch_size=32, learning_rate=0.01):
    """
    Обучение модели

    Args:
        model: экземпляр нейронной сети
        X_train, y_train: обучающие данные
        X_val, y_val: валидационные данные
        epochs: количество эпох
        batch_size: размер батча
        learning_rate: скорость обучения

    Returns:
        history: словарь с историей обучения
    """
    history = {
        'loss': [],
        'accuracy': [],
        'val_loss': [],
        'val_accuracy': []
    }

    n_train = X_train.shape[0]

    for epoch in range(epochs):
        print(f"\nЭпоха {epoch + 1}/{epochs}")

        # Перемешиваем данные в начале каждой эпохи
        indices = np.random.permutation(n_train)
        X_train_shuffled = X_train[indices]
        y_train_shuffled = y_train[indices]

        epoch_loss = 0
        epoch_accuracy = 0
        n_batches = 0

        # Обучение по батчам
        for X_batch, y_batch in tqdm(
                create_minibatches(X_train_shuffled, y_train_shuffled, batch_size),
                total=n_train // batch_size,
                desc="Обучение"
        ):
            # Один шаг обучения
            loss, y_pred = model.train_step(X_batch, y_batch, learning_rate)

            # Сбор статистики
            epoch_loss += loss
            epoch_accuracy += accuracy(y_pred, y_batch)
            n_batches += 1

        # Средние значения за эпоху
        epoch_loss /= n_batches
        epoch_accuracy /= n_batches

        # Валидация
        val_pred = model.forward(X_val)
        val_loss = model.compute_loss(val_pred, y_val)
        val_accuracy = model.evaluate(X_val, y_val)

        # Сохранение истории
        history['loss'].append(epoch_loss)
        history['accuracy'].append(epoch_accuracy)
        history['val_loss'].append(val_loss)
        history['val_accuracy'].append(val_accuracy)

        print(f"Потери: {epoch_loss:.4f}, Точность: {epoch_accuracy:.4f}")
        print(f"Валидационные потери: {val_loss:.4f}, "
              f"Валидационная точность: {val_accuracy:.4f}")

    return history


# ==================== 8. ОСНОВНАЯ ФУНКЦИЯ ====================
def main():
    """Основная функция для обучения и оценки модели"""
    # Параметры сети
    INPUT_SIZE = 784
    HIDDEN_SIZE = 128
    OUTPUT_SIZE = 10

    # Гиперпараметры обучения
    EPOCHS = 10
    BATCH_SIZE = 64
    LEARNING_RATE = 0.01

    print("=" * 60)
    print("НЕЙРОННАЯ СЕТЬ ДЛЯ КЛАССИФИКАЦИИ MNIST")
    print("=" * 60)
    print("Все компоненты в одном файле - без импортов")
    print("=" * 60)

    # Загрузка данных
    print("\n[1/4] Загрузка данных MNIST...")
    X_train, X_test, y_train, y_test, label_binarizer = load_mnist_data()

    # Разделение обучающей выборки на обучение и валидацию
    split_idx = int(0.8 * X_train.shape[0])
    X_train_final = X_train[:split_idx]
    y_train_final = y_train[:split_idx]
    X_val = X_train[split_idx:]
    y_val = y_train[split_idx:]

    print(f"   Обучающая выборка: {X_train_final.shape}")
    print(f"   Валидационная выборка: {X_val.shape}")
    print(f"   Тестовая выборка: {X_test.shape}")

    # Создание модели
    print("\n[2/4] Создание нейронной сети...")
    model = NeuralNetwork(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE)

    # Настройка оптимизатора
    optimizer = SGD(learning_rate=LEARNING_RATE, momentum=0.9)
    model.set_optimizer(optimizer)

    print(f"   Архитектура сети: {INPUT_SIZE} → {HIDDEN_SIZE} → {OUTPUT_SIZE}")
    print(f"   Функции активации: ReLU → Softmax")
    print(f"   Функция потерь: Кросс-энтропия")
    print(f"   Оптимизатор: SGD с моментумом")
    print(f"   Скорость обучения: {LEARNING_RATE}")
    print(f"   Размер батча: {BATCH_SIZE}")
    print(f"   Количество эпох: {EPOCHS}")

    # Обучение модели
    print("\n[3/4] Обучение модели...")
    history = train_model(
        model=model,
        X_train=X_train_final,
        y_train=y_train_final,
        X_val=X_val,
        y_val=y_val,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE
    )

    print("   Обучение завершено успешно!")

    # Тестирование на тестовой выборке
    print("\n[4/4] Тестирование модели...")
    test_accuracy = model.evaluate(X_test, y_test)
    print(f"   Точность на тестовой выборке: {test_accuracy:.4f} ({test_accuracy:.2%})")

    # Построение графиков обучения
    print("\nПостроение графиков обучения...")
    plot_training_history(history)
    print("   Графики сохранены в 'training_history.png'")

    # Пример предсказания для нескольких изображений
    print("\nПримеры предсказаний:")
    n_examples = 5
    indices = np.random.choice(len(X_test), n_examples, replace=False)

    correct = 0
    for i, idx in enumerate(indices):
        x_sample = X_test[idx].reshape(1, -1)
        true_label = np.argmax(y_test[idx])
        pred_label = model.predict(x_sample)[0]

        if true_label == pred_label:
            correct += 1
            status = "✓"
        else:
            status = "✗"

        print(f"   Пример {i + 1}:")
        print(f"     Истинная цифра: {true_label}")
        print(f"     Предсказанная цифра: {pred_label}")
        print(f"     Результат: {status}")

    print(f"\n   Правильно предсказано: {correct} из {n_examples}")

    print("\n" + "=" * 60)
    print(f"ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print(f"Финальная точность на тестовой выборке: {test_accuracy:.2%}")
    print("=" * 60)

    return model, history, test_accuracy


# ==================== 9. ЗАПУСК ====================
if __name__ == "__main__":
    try:
        model, history, accuracy = main()
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        import traceback

        traceback.print_exc()
        print("\nУбедитесь, что установлены все зависимости:")
        print("pip install numpy matplotlib scikit-learn tqdm")