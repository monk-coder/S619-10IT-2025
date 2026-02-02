"""
neural_network.py
Реализация нейронной сети с нуля для классификации MNIST
"""

import numpy as np
import time


class NeuralNetwork:
    """Класс нейронной сети с прямым и обратным распространением"""

    def __init__(self, layer_sizes, learning_rate=0.1, reg_lambda=0.01):
        """
        Инициализация нейронной сети

        Parameters:
        -----------
        layer_sizes : list
            Список размеров слоев (входной, скрытые, выходной)
        learning_rate : float
            Скорость обучения
        reg_lambda : float
            Параметр регуляризации L2
        """
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.reg_lambda = reg_lambda
        self.parameters = {}
        self.history = {'loss': [], 'accuracy': [], 'val_loss': [], 'val_accuracy': []}

        # Инициализация параметров
        self._initialize_parameters()

    def _initialize_parameters(self):
        """Инициализация весов и смещений"""
        np.random.seed(42)

        for i in range(1, len(self.layer_sizes)):
            # Инициализация весов методом Xavier/Glorot
            scale = np.sqrt(2.0 / self.layer_sizes[i - 1])
            self.parameters[f'W{i}'] = np.random.randn(
                self.layer_sizes[i], self.layer_sizes[i - 1]
            ) * scale

            # Инициализация смещений нулями
            self.parameters[f'b{i}'] = np.zeros((self.layer_sizes[i], 1))

    def _sigmoid(self, z):
        """Сигмоидная функция активации"""
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def _sigmoid_derivative(self, a):
        """Производная сигмоидной функции"""
        return a * (1 - a)

    def _relu(self, z):
        """ReLU функция активации"""
        return np.maximum(0, z)

    def _relu_derivative(self, z):
        """Производная ReLU функции"""
        return (z > 0).astype(float)

    def _softmax(self, z):
        """Функция активации Softmax"""
        exp_z = np.exp(z - np.max(z, axis=0, keepdims=True))  # Стабилизация
        return exp_z / np.sum(exp_z, axis=0, keepdims=True)

    def _forward_propagation(self, X):
        """
        Прямое распространение

        Returns:
        --------
        cache : dict
            Кэш с активациями и линейными комбинациями
        """
        cache = {'A0': X.T}
        A = X.T

        # Прямое распространение через скрытые слои
        L = len(self.layer_sizes) - 1

        for l in range(1, L):
            W = self.parameters[f'W{l}']
            b = self.parameters[f'b{l}']

            Z = np.dot(W, A) + b
            A = self._relu(Z)

            cache[f'Z{l}'] = Z
            cache[f'A{l}'] = A

        # Выходной слой (Softmax)
        W = self.parameters[f'W{L}']
        b = self.parameters[f'b{L}']

        Z = np.dot(W, cache[f'A{L - 1}']) + b
        A = self._softmax(Z)

        cache[f'Z{L}'] = Z
        cache[f'A{L}'] = A

        return cache

    def _compute_loss(self, AL, Y):
        """
        Вычисление функции потерь (кросс-энтропия + L2 регуляризация)
        """
        m = Y.shape[1]

        # Кросс-энтропия
        loss = -np.sum(Y * np.log(AL + 1e-8)) / m

        # L2 регуляризация
        L = len(self.layer_sizes) - 1
        reg_loss = 0
        for l in range(1, L + 1):
            W = self.parameters[f'W{l}']
            reg_loss += np.sum(W * W)

        reg_loss = (self.reg_lambda / (2 * m)) * reg_loss

        return loss + reg_loss

    def _backward_propagation(self, X, Y, cache):
        """
        Обратное распространение ошибки

        Returns:
        --------
        grads : dict
            Градиенты параметров
        """
        m = X.shape[0]
        grads = {}
        L = len(self.layer_sizes) - 1

        # Градиент выходного слоя
        AL = cache[f'A{L}']
        dZ = AL - Y.T

        grads[f'dW{L}'] = np.dot(dZ, cache[f'A{L - 1}'].T) / m
        grads[f'db{L}'] = np.sum(dZ, axis=1, keepdims=True) / m

        # Добавление регуляризации
        grads[f'dW{L}'] += (self.reg_lambda / m) * self.parameters[f'W{L}']

        # Распространение через скрытые слои
        for l in reversed(range(1, L)):
            dA = np.dot(self.parameters[f'W{l + 1}'].T, dZ)
            dZ = dA * self._relu_derivative(cache[f'Z{l}'])

            grads[f'dW{l}'] = np.dot(dZ, cache[f'A{l - 1}'].T) / m
            grads[f'db{l}'] = np.sum(dZ, axis=1, keepdims=True) / m

            # Добавление регуляризации
            grads[f'dW{l}'] += (self.reg_lambda / m) * self.parameters[f'W{l}']

        return grads

    def _update_parameters(self, grads):
        """Обновление параметров с помощью градиентного спуска"""
        L = len(self.layer_sizes) - 1

        for l in range(1, L + 1):
            self.parameters[f'W{l}'] -= self.learning_rate * grads[f'dW{l}']
            self.parameters[f'b{l}'] -= self.learning_rate * grads[f'b{l}']

    def predict(self, X):
        """Предсказание класса для входных данных"""
        cache = self._forward_propagation(X)
        AL = cache[f'A{len(self.layer_sizes) - 1}']
        predictions = np.argmax(AL, axis=0)
        return predictions

    def predict_proba(self, X):
        """Вероятности классов для входных данных"""
        cache = self._forward_propagation(X)
        AL = cache[f'A{len(self.layer_sizes) - 1}']
        return AL.T

    def compute_accuracy(self, X, Y):
        """Вычисление точности предсказаний"""
        predictions = self.predict(X)
        true_labels = np.argmax(Y, axis=1)
        accuracy = np.mean(predictions == true_labels)
        return accuracy

    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=100, batch_size=64, verbose=True):
        """
        Обучение нейронной сети

        Parameters:
        -----------
        X_train, y_train : тренировочные данные
        X_val, y_val : валидационные данные (опционально)
        epochs : количество эпох
        batch_size : размер мини-батча
        verbose : вывод информации о процессе обучения
        """
        n_samples = X_train.shape[0]
        n_batches = int(np.ceil(n_samples / batch_size))

        if verbose:
            print(f"Начало обучения:")
            print(f"  Эпох: {epochs}")
            print(f"  Размер батча: {batch_size}")
            print(f"  Количество батчей: {n_batches}")
            print("-" * 50)

        for epoch in range(epochs):
            start_time = time.time()

            # Перемешивание данных
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_loss = 0

            # Обучение по мини-батчам
            for batch in range(n_batches):
                start = batch * batch_size
                end = min(start + batch_size, n_samples)

                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # Прямое распространение
                cache = self._forward_propagation(X_batch)
                AL = cache[f'A{len(self.layer_sizes) - 1}']

                # Вычисление потерь
                batch_loss = self._compute_loss(AL, y_batch)
                epoch_loss += batch_loss

                # Обратное распространение
                grads = self._backward_propagation(X_batch, y_batch, cache)

                # Обновление параметров
                self._update_parameters(grads)

            # Средние потери за эпоху
            epoch_loss /= n_batches

            # Вычисление точности
            train_accuracy = self.compute_accuracy(X_train, y_train)

            # Сохранение истории
            self.history['loss'].append(epoch_loss)
            self.history['accuracy'].append(train_accuracy)

            # Валидация (если данные предоставлены)
            val_accuracy = None
            val_loss = None

            if X_val is not None and y_val is not None:
                cache_val = self._forward_propagation(X_val)
                AL_val = cache_val[f'A{len(self.layer_sizes) - 1}']
                val_loss = self._compute_loss(AL_val, y_val)
                val_accuracy = self.compute_accuracy(X_val, y_val)

                self.history['val_loss'].append(val_loss)
                self.history['val_accuracy'].append(val_accuracy)

            # Вывод информации
            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                epoch_time = time.time() - start_time
                output = f"Эпоха {epoch + 1:3d}/{epochs}"
                output += f" - Потери: {epoch_loss:.4f}"
                output += f" - Точность: {train_accuracy:.4f}"

                if val_accuracy is not None:
                    output += f" - Валидация: {val_accuracy:.4f}"

                output += f" - Время: {epoch_time:.2f}с"
                print(output)

        if verbose:
            print("-" * 50)
            print("Обучение завершено!")

    def get_parameters(self):
        """Получить параметры модели"""
        return self.parameters

    def set_parameters(self, params):
        """Установить параметры модели"""
        self.parameters = params