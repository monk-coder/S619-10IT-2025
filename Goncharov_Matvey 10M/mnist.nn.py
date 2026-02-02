import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split

# Загрузка данных MNIST
mnist = fetch_openml('mnist_784', version=1, parser='auto')
X = mnist.data / 255.0
y = mnist.target.astype(int)

# One-hot encoding
y_onehot = np.eye(10)[y]

# Разделение на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.2, random_state=42
)

class NeuralNetwork:
    def init(self):
        np.random.seed(67)
        self.W1 = np.random.randn(784, 128) * np.sqrt(2/784)
        self.b1 = np.zeros((1, 128))
        self.W2 = np.random.randn(128, 64) * np.sqrt(2/128)
        self.b2 = np.zeros((1, 64))
        self.W3 = np.random.randn(64, 10) * np.sqrt(2/64)
        self.b3 = np.zeros((1, 10))
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        """Прямой проход"""
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.relu(self.z2)
        self.z3 = self.a2 @ self.W3 + self.b3
        return self.softmax(self.z3)
    
    def compute_loss(self, output, y_true):
        """Cross-entropy loss с защитой от log(0)"""
        epsilon = 1e-12
        return -np.mean(np.sum(y_true * np.log(output + epsilon), axis=1))
    
    def backward(self, X_batch, y_batch, output):
        """
        Обратное распространение ошибки.
        Возвращает словарь с градиентами.
        """
        batch_size = X_batch.shape[0]
        
        # Градиенты для выходного слоя
        dz3 = output - y_batch
        dW3 = self.a2.T @ dz3 / batch_size
        db3 = np.sum(dz3, axis=0, keepdims=True) / batch_size
        
        # Градиенты для второго скрытого слоя
        dz2 = (dz3 @ self.W3.T) * (self.a2 > 0)  # ReLU derivative
        dW2 = self.a1.T @ dz2 / batch_size
        db2 = np.sum(dz2, axis=0, keepdims=True) / batch_size
        
        # Градиенты для первого скрытого слоя
        dz1 = (dz2 @ self.W2.T) * (self.a1 > 0)  # ReLU derivative
        dW1 = X_batch.T @ dz1 / batch_size
        db1 = np.sum(dz1, axis=0, keepdims=True) / batch_size
        
        return {
            'dW1': dW1, 'db1': db1,
            'dW2': dW2, 'db2': db2,
            'dW3': dW3, 'db3': db3
        }
    
    def update_weights(self, gradients, lr):
        """Обновление весов методом градиентного спуска"""
        self.W1 -= lr * gradients['dW1']
        self.b1 -= lr * gradients['db1']
        self.W2 -= lr * gradients['dW2']
        self.b2 -= lr * gradients['db2']
        self.W3 -= lr * gradients['dW3']
        self.b3 -= lr * gradients['db3']
        def train(self, X, y, epochs=20, lr=0.01, batch_size=64):
        n_samples = X.shape[0]
        
        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            total_loss = 0
            
            # Мини-батч обучение
            for i in range(0, n_samples, batch_size):
                batch_idx = indices[i:i+batch_size]
                X_batch, y_batch = X[batch_idx], y[batch_idx]
                
                # Прямой проход
                output = self.forward(X_batch)
                
                # Расчёт потерь
                loss = self.compute_loss(output, y_batch)
                total_loss += loss * len(batch_idx)
                
                # Обратный проход и обновление весов
                gradients = self.backward(X_batch, y_batch, output)
                self.update_weights(gradients, lr)
            
            # Вывод метрик каждые 5 эпох
            if epoch % 5 == 0:
                train_pred = self.forward(X_train)
                train_acc = np.mean(
                    np.argmax(train_pred, axis=1) == np.argmax(y_train, axis=1)
                )
                avg_loss = total_loss / n_samples
                print(f"Epoch {epoch:2d} | Loss: {avg_loss:.4f} | Train Accuracy: {train_acc:.4f}")
    
    def predict(self, X):
        """Получение предсказаний (классов)"""
        probs = self.forward(X)
        return np.argmax(probs, axis=1)

# Инициализация и обучение сети
nn = NeuralNetwork()
nn.train(X_train, y_train, epochs=20, lr=0.01, batch_size=64)

# Тестирование
test_pred = nn.forward(X_test)
test_acc = np.mean(np.argmax(test_pred, axis=1) == np.argmax(y_test, axis=1))
print(f"\n{'='*60}")
print(f"Final Test Accuracy: {test_acc:.4f}")
print(f"{'='*60}")
