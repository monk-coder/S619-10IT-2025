import numpy as np


class NeuralNetwork:
    def __init__(self, input_size=784, hidden_size=128, output_size=10,
                 learning_rate=0.1, reg_lambda=0.001):
        """
        Инициализация нейронной сети

        Параметры:
        - input_size: размер входного слоя (28x28=784 для MNIST)
        - hidden_size: размер скрытого слоя
        - output_size: размер выходного слоя (10 цифр)
        - learning_rate: скорость обучения
        - reg_lambda: параметр регуляризации L2
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        self.reg_lambda = reg_lambda

        # Инициализация весов небольшими случайными значениями
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))

    def sigmoid(self, x):
        """Сигмоидная функция активации"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def sigmoid_derivative(self, x):
        """Производная сигмоидной функции"""
        return x * (1 - x)

    def softmax(self, x):
        """Функция softmax для многоклассовой классификации"""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, X):
        """Прямое распространение"""
        # Скрытый слой
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.sigmoid(self.z1)

        # Выходной слой
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.softmax(self.z2)

        return self.a2

    def compute_loss(self, y_pred, y_true):
        """Вычисление функции потерь (кросс-энтропия) с регуляризацией L2"""
        m = y_true.shape[0]

        # Кросс-энтропия
        log_likelihood = -np.log(y_pred[range(m), y_true])
        loss = np.sum(log_likelihood) / m

        # Регуляризация L2
        reg_loss = (self.reg_lambda / (2 * m)) * (
                np.sum(np.square(self.W1)) + np.sum(np.square(self.W2))
        )

        return loss + reg_loss

    def backward(self, X, y_true, y_pred):
        """Обратное распространение ошибки"""
        m = X.shape[0]

        # Ошибка на выходном слое
        delta2 = y_pred.copy()
        delta2[range(m), y_true] -= 1
        delta2 /= m

        # Градиенты для выходного слоя
        dW2 = np.dot(self.a1.T, delta2) + (self.reg_lambda / m) * self.W2
        db2 = np.sum(delta2, axis=0, keepdims=True)

        # Ошибка на скрытом слое
        delta1 = np.dot(delta2, self.W2.T) * self.sigmoid_derivative(self.a1)

        # Градиенты для скрытого слоя
        dW1 = np.dot(X.T, delta1) + (self.reg_lambda / m) * self.W1
        db1 = np.sum(delta1, axis=0, keepdims=True)

        return dW1, db1, dW2, db2

    def update_parameters(self, dW1, db1, dW2, db2):
        """Обновление весов с помощью градиентного спуска"""
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2

    def train(self, X_train, y_train, X_val, y_val,
              epochs=50, batch_size=32, verbose=True):
        """Обучение нейронной сети"""
        n_samples = X_train.shape[0]
        history = {
            'loss': [], 'accuracy': [],
            'val_loss': [], 'val_accuracy': []
        }

        for epoch in range(epochs):
            # Перемешивание данных
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_loss = 0
            correct_predictions = 0

            # Мини-батчи
            for i in range(0, n_samples, batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                y_batch = y_shuffled[i:i + batch_size]

                # Прямое распространение
                y_pred = self.forward(X_batch)

                # Вычисление потерь
                batch_loss = self.compute_loss(y_pred, y_batch)
                epoch_loss += batch_loss * X_batch.shape[0]

                # Обратное распространение
                dW1, db1, dW2, db2 = self.backward(X_batch, y_batch, y_pred)

                # Обновление весов
                self.update_parameters(dW1, db1, dW2, db2)

                # Подсчет правильных предсказаний
                predictions = np.argmax(y_pred, axis=1)
                correct_predictions += np.sum(predictions == y_batch)

            # Средняя потеря и точность на эпохе
            avg_loss = epoch_loss / n_samples
            accuracy = correct_predictions / n_samples

            # Валидация
            val_loss, val_accuracy = self.evaluate(X_val, y_val)

            # Сохранение истории
            history['loss'].append(avg_loss)
            history['accuracy'].append(accuracy)
            history['val_loss'].append(val_loss)
            history['val_accuracy'].append(val_accuracy)

            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                print(f"Epoch {epoch + 1}/{epochs}:")
                print(f"  Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}")
                print(f"  Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}")

        return history

    def predict(self, X):
        """Предсказание для новых данных"""
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

    def evaluate(self, X, y):
        """Оценка точности модели"""
        y_pred = self.forward(X)
        loss = self.compute_loss(y_pred, y)
        predictions = np.argmax(y_pred, axis=1)
        accuracy = np.mean(predictions == y)

        return loss, accuracy