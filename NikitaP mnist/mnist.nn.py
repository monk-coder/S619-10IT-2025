import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical

class NeuralNetwork:
    def __init__(self, layer_sizes, lr=0.01):
        self.weights = []
        self.biases = []
        for i in range(len(layer_sizes)-1):
            limit = np.sqrt(6/(layer_sizes[i]+layer_sizes[i+1]))
            self.weights.append(np.random.uniform(-limit, limit, (layer_sizes[i], layer_sizes[i+1])))
            self.biases.append(np.zeros((1, layer_sizes[i+1])))
        self.lr = lr
        self.cache = {}
    
    def relu(self, x): return np.maximum(0, x)
    def relu_deriv(self, x): return (x > 0).astype(float)
    def softmax(self, x):
        exp = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp / np.sum(exp, axis=1, keepdims=True)
    
    def forward(self, X):
        self.cache['A0'] = X
        for i in range(len(self.weights)-1):
            Z = self.cache[f'A{i}'] @ self.weights[i] + self.biases[i]
            self.cache[f'A{i+1}'] = self.relu(Z)
        Z_out = self.cache[f'A{len(self.weights)-1}'] @ self.weights[-1] + self.biases[-1]
        return self.softmax(Z_out)
    
    def backward(self, X, y):
        m = X.shape[0]
        A_out = self.forward(X)
        dZ = A_out - y
        
        dW = []
        db = []
        for l in range(len(self.weights)-1, -1, -1):
            A_prev = self.cache[f'A{l}'] if l > 0 else X
            dW.insert(0, (A_prev.T @ dZ) / m)
            db.insert(0, np.sum(dZ, axis=0, keepdims=True) / m)
            if l > 0:
                dZ = (dZ @ self.weights[l].T) * self.relu_deriv(self.cache[f'A{l}'])
        
        for i in range(len(self.weights)):
            self.weights[i] -= self.lr * dW[i]
            self.biases[i] -= self.lr * db[i]
        
        loss = -np.sum(y * np.log(A_out + 1e-12)) / m
        acc = np.mean(np.argmax(A_out, axis=1) == np.argmax(y, axis=1))
        return loss, acc
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch=64):
        for epoch in range(epochs):
            idx = np.random.permutation(len(X_train))
            X_shuffled, y_shuffled = X_train[idx], y_train[idx]
            
            for i in range(0, len(X_train), batch):
                X_batch = X_shuffled[i:i+batch]
                y_batch = y_shuffled[i:i+batch]
                self.backward(X_batch, y_batch)
            
            if epoch % 10 == 0:
                val_pred = self.forward(X_val)
                val_acc = np.mean(np.argmax(val_pred, axis=1) == np.argmax(y_val, axis=1))
                print(f"Epoch {epoch}: Val Acc = {val_acc:.4f}")

# Загрузка данных
(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train = X_train.reshape(-1, 784).astype('float32') / 255
X_test = X_test.reshape(-1, 784).astype('float32') / 255
y_train = to_categorical(y_train, 10)
y_test = to_categorical(y_test, 10)

# Обучение
nn = NeuralNetwork([784, 128, 64, 10], lr=0.01)
nn.train(X_train, y_train, X_test, y_test, epochs=50)

# Тестирование
test_pred = nn.forward(X_test)
test_acc = np.mean(np.argmax(test_pred, axis=1) == np.argmax(y_test, axis=1))
print(f"\nTest Accuracy: {test_acc:.4f}")
