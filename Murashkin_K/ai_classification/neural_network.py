import numpy as np


class SimpleNeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        self.W1 = np.random.randn(hidden_size, input_size) * np.sqrt(2. / input_size)
        self.b1 = np.zeros((hidden_size, 1))

        self.W2 = np.random.randn(output_size, hidden_size) * np.sqrt(2. / hidden_size)
        self.b2 = np.zeros((output_size, 1))

    def relu(self, Z):
        return np.maximum(0, Z)

    def relu_deriv(self, Z):
        return Z > 0

    def softmax(self, Z):
        exp_Z = np.exp(Z - np.max(Z, axis=0, keepdims=True))
        return exp_Z / np.sum(exp_Z, axis=0, keepdims=True)

    def forward_propagation(self, X):
        Z1 = np.dot(self.W1, X) + self.b1
        A1 = self.relu(Z1)

        Z2 = np.dot(self.W2, A1) + self.b2
        A2 = self.softmax(Z2)

        cache = {"Z1": Z1, "A1": A1, "Z2": Z2, "A2": A2}
        return A2, cache

    def one_hot(self, Y):
        one_hot_Y = np.zeros((Y.max() + 1, Y.size))
        one_hot_Y[Y, np.arange(Y.size)] = 1
        return one_hot_Y

    def backward_propagation(self, X, Y, cache):
        m = X.shape[1]
        one_hot_Y = self.one_hot(Y)
        A1 = cache["A1"]
        A2 = cache["A2"]
        Z1 = cache["Z1"]

        dZ2 = A2 - one_hot_Y

        dW2 = (1 / m) * np.dot(dZ2, A1.T)
        db2 = (1 / m) * np.sum(dZ2, axis=1, keepdims=True)

        dZ1 = np.dot(self.W2.T, dZ2) * self.relu_deriv(Z1)

        dW1 = (1 / m) * np.dot(dZ1, X.T)
        db1 = (1 / m) * np.sum(dZ1, axis=1, keepdims=True)

        return {"dW1": dW1, "db1": db1, "dW2": dW2, "db2": db2}

    def update_params(self, grads):
        self.W1 -= self.learning_rate * grads["dW1"]
        self.b1 -= self.learning_rate * grads["db1"]
        self.W2 -= self.learning_rate * grads["dW2"]
        self.b2 -= self.learning_rate * grads["db2"]

    def compute_loss(self, A2, Y):
        m = Y.shape[0]
        one_hot_Y = self.one_hot(Y)
        log_probs = np.multiply(np.log(A2 + 1e-15), one_hot_Y)
        cost = - np.sum(log_probs) / m
        return cost

    def get_predictions(self, A2):
        return np.argmax(A2, axis=0)

    def get_accuracy(self, predictions, Y):
        return np.sum(predictions == Y) / Y.size