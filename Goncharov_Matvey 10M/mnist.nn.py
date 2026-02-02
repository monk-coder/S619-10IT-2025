import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split

# Загрузка данных
mnist = fetch_openml('mnist_784', version=1, parser='auto')
X = mnist.data / 255.0
y = mnist.target.astype(int)

# One-hot encoding
y_onehot = np.eye(10)[y]

# Разделение
X_train, X_test, y_train, y_test = train_test_split(X, y_onehot, test_size=0.2, random_state=42)

class NeuralNetwork:
    def __init__(self):
        np.random.seed(67)
        self.W1 = np.random.randn(784, 128) * np.sqrt(2/784)
        self.b1 = np.zeros((1, 128))
        self.W2 = np.random.randn(128, 64) * np.sqrt(2/128)
        self.b2 = np.zeros((1, 64))
        self.W3 = np.random.randn(64, 10) * np.sqrt(2/64)
        self.b3 = np.zeros((1, 10))
    
    def relu(self, x): return np.maximum(0, x)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.relu(self.z2)
        self.z3 = self.a2 @ self.W3 + self.b3
        return self.softmax(self.z3)
    
    def train(self, X, y, epochs=20, lr=0.01, batch_size=64):
        for epoch in range(epochs):
            indices = np.random.permutation(len(X))
            for i in range(0, len(X), batch_size):
                batch_idx = indices[i:i+batch_size]
                X_batch, y_batch = X[batch_idx], y[batch_idx]
                
                # Forward
                output = self.forward(X_batch)
                
                # Backward
                dz3 = output - y_batch
                dW3 = self.a2.T @ dz3 / batch_size
                db3 = np.sum(dz3, axis=0, keepdims=True) / batch_size
                
                dz2 = (dz3 @ self.W3.T) * (self.a2 > 0)
                dW2 = self.a1.T @ dz2 / batch_size
                db2 = np.sum(dz2, axis=0, keepdims=True) / batch_size
                
                dz1 = (dz2 @ self.W2.T) * (self.a1 > 0)
                dW1 = X_batch.T @ dz1 / batch_size
                db1 = np.sum(dz1, axis=0, keepdims=True) / batch_size
                
                # Update weights
                self.W1 -= lr * dW1
                self.b1 -= lr * db1
                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W3 -= lr * dW3
                self.b3 -= lr * db3
            
            if epoch % 5 == 0:
                pred = self.forward(X_train[:1000])
                acc = np.mean(np.argmax(pred, axis=1) == np.argmax(y_train[:1000], axis=1))
                print(f"Epoch {epoch}: Accuracy = {acc:.4f}")

# Обучение
nn = NeuralNetwork()
nn.train(X_train, y_train, epochs=20, lr=0.01)

# Тестирование
test_pred = nn.forward(X_test)
test_acc = np.mean(np.argmax(test_pred, axis=1) == np.argmax(y_test, axis=1))
print(f"\nTest Accuracy: {test_acc:.4f}")
