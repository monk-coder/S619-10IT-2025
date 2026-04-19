import numpy as np

INPUT_SIZE = 784
HIDDEN_SIZE = 128
OUTPUT_SIZE = 10
DEFAULT_LR = 0.01
WEIGHT_INIT_SCALE = 0.01


class NeuralNetwork:
    def __init__(self, lr=DEFAULT_LR):
        self.lr = lr
        self.W1 = np.random.randn(INPUT_SIZE, HIDDEN_SIZE) * WEIGHT_INIT_SCALE
        self.b1 = np.zeros((1, HIDDEN_SIZE))
        self.W2 = np.random.randn(HIDDEN_SIZE, OUTPUT_SIZE) * WEIGHT_INIT_SCALE
        self.b2 = np.zeros((1, OUTPUT_SIZE))

    def relu(self, x):
        return np.maximum(0, x)

    def relu_deriv(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, X):
        self.Z1 = X @ self.W1 + self.b1
        self.A1 = self.relu(self.Z1)
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = self.softmax(self.Z2)
        return self.A2

    def compute_loss(self, y_true, y_pred):
        m = y_true.shape[0]
        log_likelihood = -np.log(y_pred[range(m), y_true])
        return np.sum(log_likelihood) / m

    def backward(self, X, y_true):
        m = X.shape[0]
        y_one = np.zeros_like(self.A2)
        y_one[np.arange(m), y_true] = 1

        dZ2 = (self.A2 - y_one) / m
        dW2 = self.A1.T @ dZ2
        db2 = np.sum(dZ2, axis=0, keepdims=True)

        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * self.relu_deriv(self.Z1)

        dW1 = X.T @ dZ1
        db1 = np.sum(dZ1, axis=0, keepdims=True)

        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2

    def predict(self, X):
        probs = self.forward(X)
        return np.argmax(probs, axis=1)

    def accuracy(self, X, y):
        preds = self.predict(X)
        return np.mean(preds == y)