import numpy as np
import pickle
import os
from tqdm import tqdm


class NeuralNetwork:
    """
    Полносвязная нейронная сеть для классификации рукописных цифр MNIST
    """

    def __init__(self, layer_sizes, learning_rate=0.01, regularization=0.001):
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.num_layers = len(layer_sizes)

        # Инициализация весов и смещений
        self.weights = []
        self.biases = []

        for i in range(1, self.num_layers):
            if i < self.num_layers - 1:
                # He initialization for ReLU
                limit = np.sqrt(2.0 / layer_sizes[i - 1])
                weight = np.random.randn(layer_sizes[i], layer_sizes[i - 1]) * limit
            else:
                # Xavier initialization for output layer
                limit = np.sqrt(1.0 / layer_sizes[i - 1])
                weight = np.random.randn(layer_sizes[i], layer_sizes[i - 1]) * limit

            bias = np.zeros((layer_sizes[i], 1))
            self.weights.append(weight)
            self.biases.append(bias)

    def sigmoid(self, z):  # УДАЛИТЬ эту функцию если не используется
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
        activations = [X]
        Zs = []

        for i in range(self.num_layers - 2):
            Z = self.weights[i] @ activations[-1] + self.biases[i]
            A = self.relu(Z)
            Zs.append(Z)
            activations.append(A)

        Z = self.weights[-1] @ activations[-1] + self.biases[-1]
        A = self.softmax(Z)
        Zs.append(Z)
        activations.append(A)

        return activations, Zs

    def compute_loss(self, Y_pred, Y_true):
        m = Y_true.shape[1]

        epsilon = 1e-15
        Y_pred = np.clip(Y_pred, epsilon, 1 - epsilon)
        cross_entropy = -np.sum(Y_true * np.log(Y_pred)) / m

        l2_penalty = 0
        for weight in self.weights:
            l2_penalty += np.sum(np.square(weight))
        l2_penalty = (self.regularization / (2 * m)) * l2_penalty

        return cross_entropy + l2_penalty

    def relu_derivative(self, z):
        return (z > 0).astype(float)

    def backward_propagation(self, X, Y, activations, Zs):
        m = X.shape[1]
        # ИЗМЕНЕНИЕ 2: Создаем список градиентов правильной длины
        dW = [None] * len(self.weights)
        db = [None] * len(self.biases)

        L = self.num_layers - 1

        # Градиент выходного слоя
        dZ = activations[-1] - Y
        dW[-1] = (dZ @ activations[-2].T) / m + (self.regularization / m) * self.weights[-1]
        db[-1] = np.sum(dZ, axis=1, keepdims=True) / m

        # Обратное распространение через скрытые слои
        for l in range(L - 2, -1, -1):
            dA = self.weights[l + 1].T @ dZ
            dZ = dA * self.relu_derivative(Zs[l])
            dW[l] = (dZ @ activations[l].T) / m + (self.regularization / m) * self.weights[l]
            db[l] = np.sum(dZ, axis=1, keepdims=True) / m

        # ИЗМЕНЕНИЕ 2: Возвращаем как словарь со списками
        return {'dW': dW, 'db': db}

    def update_parameters(self, grads):
        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * grads['dW'][i]
            self.biases[i] -= self.learning_rate * grads['db'][i]

    def predict(self, X):
        activations, _ = self.forward_propagation(X)
        return np.argmax(activations[-1], axis=0)

    def accuracy(self, X, Y):
        if Y.ndim == 2:
            Y_labels = np.argmax(Y, axis=0)
        else:
            Y_labels = Y

        predictions = self.predict(X)
        return np.mean(predictions == Y_labels)

    def train(self, X_train, Y_train, X_val, Y_val, epochs=50, batch_size=32):
        m = X_train.shape[1]
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_accuracy': [],
            'val_accuracy': []
        }

        print("Начало обучения...")
        for epoch in range(epochs):
            permutation = np.random.permutation(m)
            X_shuffled = X_train[:, permutation]
            Y_shuffled = Y_train[:, permutation]

            epoch_loss = 0
            num_batches = m // batch_size

            with tqdm(total=num_batches, desc=f'Epoch {epoch + 1}/{epochs}') as pbar:
                for i in range(0, m, batch_size):
                    X_batch = X_shuffled[:, i:i + batch_size]
                    Y_batch = Y_shuffled[:, i:i + batch_size]

                    activations, Zs = self.forward_propagation(X_batch)
                    batch_loss = self.compute_loss(activations[-1], Y_batch)
                    epoch_loss += batch_loss

                    grads = self.backward_propagation(X_batch, Y_batch, activations, Zs)
                    self.update_parameters(grads)

                    pbar.update(1)
                    pbar.set_postfix({'batch_loss': f'{batch_loss:.4f}'})

            avg_train_loss = epoch_loss / num_batches
            val_activations, _ = self.forward_propagation(X_val)
            val_loss = self.compute_loss(val_activations[-1], Y_val)
            train_accuracy = self.accuracy(X_train, Y_train)
            val_accuracy = self.accuracy(X_val, Y_val)

            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(val_loss)
            history['train_accuracy'].append(train_accuracy)
            history['val_accuracy'].append(val_accuracy)

            print(
                f"Epoch {epoch + 1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}, Train Acc: {train_accuracy:.4f}, Val Acc: {val_accuracy:.4f}")

        return history

    def save_model(self, filepath):
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