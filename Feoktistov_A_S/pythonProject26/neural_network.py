import numpy as np


class NeuralNetwork:
    def __init__(self, input_size=784, hidden_size=128, output_size=10,
                 learning_rate=0.1, reg_lambda=0.001):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        self.reg_lambda = reg_lambda

        # Инициализация весов
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def sigmoid_derivative(self, x):
        return x * (1 - x)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.sigmoid(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.softmax(self.z2)
        return self.a2

    def compute_loss(self, y_pred, y_true):
        m = y_true.shape[0]
        log_likelihood = -np.log(y_pred[range(m), y_true])
        loss = np.sum(log_likelihood) / m
        reg_loss = (self.reg_lambda / (2 * m)) * (
                np.sum(np.square(self.W1)) + np.sum(np.square(self.W2))
        )
        return loss + reg_loss

    def backward(self, X, y_true, y_pred):
        m = X.shape[0]
        delta2 = y_pred.copy()
        delta2[range(m), y_true] -= 1
        delta2 /= m

        dW2 = np.dot(self.a1.T, delta2) + (self.reg_lambda / m) * self.W2
        db2 = np.sum(delta2, axis=0, keepdims=True)

        delta1 = np.dot(delta2, self.W2.T) * self.sigmoid_derivative(self.a1)
        dW1 = np.dot(X.T, delta1) + (self.reg_lambda / m) * self.W1
        db1 = np.sum(delta1, axis=0, keepdims=True)

        return dW1, db1, dW2, db2

    def update_parameters(self, dW1, db1, dW2, db2):
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2

    def train(self, X_train, y_train, X_val, y_val,
              epochs=50, batch_size=32, verbose=True):
        n_samples = X_train.shape[0]
        history = {
            'loss': [], 'accuracy': [],
            'val_loss': [], 'val_accuracy': []
        }

        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_loss = 0
            correct = 0

            for i in range(0, n_samples, batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                y_batch = y_shuffled[i:i + batch_size]

                y_pred = self.forward(X_batch)
                epoch_loss += self.compute_loss(y_pred, y_batch) * len(X_batch)
                correct += np.sum(np.argmax(y_pred, axis=1) == y_batch)

                # Оптимизированный вызов
                self.update_parameters(*self.backward(X_batch, y_batch, y_pred))

            avg_loss = epoch_loss / n_samples
            accuracy = correct / n_samples

            val_loss, val_accuracy = self.evaluate(X_val, y_val)

            history['loss'].append(avg_loss)
            history['accuracy'].append(accuracy)
            history['val_loss'].append(val_loss)
            history['val_accuracy'].append(val_accuracy)

            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                print(f"Epoch {epoch + 1}/{epochs}: Loss={avg_loss:.4f}, Acc={accuracy:.4f}, "
                      f"Val Loss={val_loss:.4f}, Val Acc={val_accuracy:.4f}")

        return history

    def predict(self, X):
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

    def evaluate(self, X, y):
        y_pred = self.forward(X)
        loss = self.compute_loss(y_pred, y)
        predictions = np.argmax(y_pred, axis=1)
        accuracy = np.mean(predictions == y)
        return loss, accuracy
