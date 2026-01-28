import numpy as np
import pickle
from tqdm import tqdm


class NeuralNetwork:
    """
    Полносвязная нейронная сеть для классификации рукописных цифр MNIST
    """

    def __init__(self, layer_sizes, learning_rate=0.01, regularization=0.001):
        """
        Инициализация нейронной сети
        """
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.num_layers = len(layer_sizes)

        # Инициализация весов и смещений
        self.weights = []
        self.biases = []

        # Инициализация He для ReLU и Xavier для выходного слоя
        for i in range(1, self.num_layers):
            if i < self.num_layers - 1:
                limit = np.sqrt(2.0 / layer_sizes[i - 1])
                weight = np.random.randn(layer_sizes[i], layer_sizes[i - 1]) * limit
            else:
                limit = np.sqrt(1.0 / layer_sizes[i - 1])
                weight = np.random.randn(layer_sizes[i], layer_sizes[i - 1]) * limit

            bias = np.zeros((layer_sizes[i], 1))

            self.weights.append(weight)
            self.biases.append(bias)

    def sigmoid(self, z):
        """Сигмоидальная функция активации"""
        return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))

    def relu(self, z):
        """ReLU функция активации"""
        return np.maximum(0, z)

    def softmax(self, z):
        """Softmax функция активации"""
        exp_z = np.exp(z - np.max(z, axis=0, keepdims=True))
        return exp_z / np.sum(exp_z, axis=0, keepdims=True)

    def forward_propagation(self, X):
        """
        Прямое распространение
        """
        activations = [X]  # A0
        Zs = []  # Z1, Z2, ..., Zn

        # Проход через скрытые слои (ReLU активация)
        for i in range(self.num_layers - 2):
            Z = self.weights[i] @ activations[-1] + self.biases[i]
            A = self.relu(Z)
            Zs.append(Z)
            activations.append(A)

        # Выходной слой (Softmax активация)
        Z = self.weights[-1] @ activations[-1] + self.biases[-1]
        A = self.softmax(Z)
        Zs.append(Z)
        activations.append(A)

        return activations, Zs

    def compute_loss(self, Y_pred, Y_true):
        """
        Вычисление кросс-энтропии с L2 регуляризацией
        """
        m = Y_true.shape[1]

        # Кросс-энтропия
        epsilon = 1e-15
        Y_pred = np.clip(Y_pred, epsilon, 1 - epsilon)
        cross_entropy = -np.sum(Y_true * np.log(Y_pred)) / m

        # L2 регуляризация
        l2_penalty = 0
        for weight in self.weights:
            l2_penalty += np.sum(np.square(weight))
        l2_penalty = (self.regularization / (2 * m)) * l2_penalty

        return cross_entropy + l2_penalty

    def relu_derivative(self, z):
        """Производная ReLU функции"""
        return (z > 0).astype(float)

    def backward_propagation(self, X, Y, activations, Zs):
        """
        Обратное распространение ошибки
        """
        m = X.shape[1]
        grads = {'dW': [], 'db': []}

        # Количество слоев (без входного)
        L = self.num_layers - 1

        # Градиент выходного слоя
        dZ = activations[-1] - Y

        # Для выходного слоя
        dW = (dZ @ activations[-2].T) / m
        db = np.sum(dZ, axis=1, keepdims=True) / m

        # Добавляем регуляризацию
        dW += (self.regularization / m) * self.weights[-1]

        # Сохраняем градиенты (в обратном порядке - от выходного к входному)
        grads['dW'].append(dW)
        grads['db'].append(db)

        # Обратное распространение через скрытые слои
        for l in range(L - 2, -1, -1):
            # dA для текущего слоя
            dA = self.weights[l + 1].T @ dZ

            # dZ для текущего скрытого слоя (ReLU)
            dZ = dA * self.relu_derivative(Zs[l])

            # Градиенты для текущего слоя
            dW = (dZ @ activations[l].T) / m
            db = np.sum(dZ, axis=1, keepdims=True) / m

            # Добавляем регуляризацию
            dW += (self.regularization / m) * self.weights[l]

            # Сохраняем градиенты (они будут в обратном порядке)
            grads['dW'].append(dW)
            grads['db'].append(db)

        # Градиенты сейчас в обратном порядке: [выходной слой, ..., первый скрытый слой]
        # Нам нужно их перевернуть, чтобы порядок соответствовал self.weights
        grads['dW'] = grads['dW'][::-1]
        grads['db'] = grads['db'][::-1]

        return grads

    def update_parameters(self, grads):
        """
        Обновление параметров с помощью градиентного спуска
        """
        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * grads['dW'][i]
            self.biases[i] -= self.learning_rate * grads['db'][i]

    def predict(self, X):
        """
        Предсказание класса для входных данных
        """
        activations, _ = self.forward_propagation(X)
        predictions = np.argmax(activations[-1], axis=0)
        return predictions

    def accuracy(self, X, Y):
        """
        Вычисление точности
        """
        if Y.ndim == 2:  # Если one-hot encoding
            Y_labels = np.argmax(Y, axis=0)
        else:  # Если уже индексы
            Y_labels = Y

        predictions = self.predict(X)
        accuracy = np.mean(predictions == Y_labels)
        return accuracy

    def train(self, X_train, Y_train, X_val, Y_val, epochs=50, batch_size=32):
        """
        Обучение нейронной сети
        """
        m = X_train.shape[1]
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_accuracy': [],
            'val_accuracy': []
        }

        print("Начало обучения...")
        for epoch in range(epochs):
            # Перемешивание данных
            permutation = np.random.permutation(m)
            X_shuffled = X_train[:, permutation]
            Y_shuffled = Y_train[:, permutation]

            epoch_loss = 0
            num_batches = m // batch_size

            with tqdm(total=num_batches, desc=f'Epoch {epoch + 1}/{epochs}') as pbar:
                for i in range(0, m, batch_size):
                    # Получение мини-батча
                    X_batch = X_shuffled[:, i:i + batch_size]
                    Y_batch = Y_shuffled[:, i:i + batch_size]

                    # Прямое распространение
                    activations, Zs = self.forward_propagation(X_batch)

                    # Вычисление потерь
                    batch_loss = self.compute_loss(activations[-1], Y_batch)
                    epoch_loss += batch_loss

                    # Обратное распространение
                    grads = self.backward_propagation(X_batch, Y_batch, activations, Zs)

                    # Обновление параметров
                    self.update_parameters(grads)

                    pbar.update(1)
                    pbar.set_postfix({'batch_loss': f'{batch_loss:.4f}'})

            # Средняя потеря за эпоху
            avg_train_loss = epoch_loss / num_batches

            # Оценка на валидационном наборе
            val_activations, _ = self.forward_propagation(X_val)
            val_loss = self.compute_loss(val_activations[-1], Y_val)
            train_accuracy = self.accuracy(X_train, Y_train)
            val_accuracy = self.accuracy(X_val, Y_val)

            # Сохранение истории
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(val_loss)
            history['train_accuracy'].append(train_accuracy)
            history['val_accuracy'].append(val_accuracy)

            print(f"Epoch {epoch + 1}/{epochs} - "
                  f"Train Loss: {avg_train_loss:.4f}, "
                  f"Val Loss: {val_loss:.4f}, "
                  f"Train Acc: {train_accuracy:.4f}, "
                  f"Val Acc: {val_accuracy:.4f}")

        return history

    def save_model(self, filepath):
        """Сохранение модели в файл"""
        model_data = {
            'layer_sizes': self.layer_sizes,
            'weights': self.weights,
            'biases': self.biases,
            'learning_rate': self.learning_rate,
            'regularization': self.regularization
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Модель сохранена в {filepath}")

    @classmethod
    def load_model(cls, filepath):
        """Загрузка модели из файла"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        model = cls(
            model_data['layer_sizes'],
            model_data['learning_rate'],
            model_data['regularization']
        )

        model.weights = model_data['weights']
        model.biases = model_data['biases']

        print(f"Модель загружена из {filepath}")
        return model