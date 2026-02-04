import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split

# Данные
mnist = fetch_openml('mnist_784', version=1, parser='auto')
X = mnist.data.astype('float32') / 255.0
y = mnist.target.astype('int')
y_onehot = np.eye(10)[y]

# Разделение
X_train, X_test, y_train, y_test = train_test_split(X, y_onehot, test_size=10000, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=10000, random_state=42)

class NeuralNetwork:
    def __init__(self):
        np.random.seed(42)
        self.W1 = np.random.randn(784, 128) * np.sqrt(2/784)
        self.b1 = np.zeros((1, 128))
        self.W2 = np.random.randn(128, 64) * np.sqrt(2/128)
        self.b2 = np.zeros((1, 64))
        self.W3 = np.random.randn(64, 10) * np.sqrt(2/64)
        self.b3 = np.zeros((1, 10))
        self.lr = 0.01
    
    def relu(self, x): return np.maximum(0, x)
    def relu_deriv(self, x): return (x > 0).astype(float)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        # Сохраняем для backprop
        self.A0 = X
        self.Z1 = X @ self.W1 + self.b1
        self.A1 = self.relu(self.Z1)
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = self.relu(self.Z2)
        self.Z3 = self.A2 @ self.W3 + self.b3
        return self.softmax(self.Z3)
    
    def backward(self, X, y):
        m = X.shape[0]
        output = self.forward(X)
        
        # Выходной слой
        dZ3 = output - y
        dW3 = self.A2.T @ dZ3 / m
        db3 = np.sum(dZ3, axis=0, keepdims=True) / m
        
        # Скрытый слой 2
        dA2 = dZ3 @ self.W3.T
        dZ2 = dA2 * self.relu_deriv(self.Z2)
        dW2 = self.A1.T @ dZ2 / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        
        # Скрытый слой 1
        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * self.relu_deriv(self.Z1)
        dW1 = self.A0.T @ dZ1 / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        
        # Обновление
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3
        
        loss = -np.sum(y * np.log(output + 1e-12)) / m
        acc = np.mean(np.argmax(output, axis=1) == np.argmax(y, axis=1))
        return loss, acc
    
    def train(self, X_train, y_train, X_val, y_val, epochs=30, batch_size=64):
        train_losses, val_losses = [], []
        train_accs, val_accs = [], []
        
        for epoch in range(epochs):
            # Перемешиваем
            idx = np.random.permutation(len(X_train))
            X_shuffled, y_shuffled = X_train[idx], y_train[idx]
            
            epoch_loss, epoch_acc = 0, 0
            
            # Мини-батчи
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                loss, acc = self.backward(X_batch, y_batch)
                epoch_loss += loss * len(X_batch)
                epoch_acc += acc * len(X_batch)
            
            # Среднее за эпоху
            epoch_loss /= len(X_train)
            epoch_acc /= len(X_train)
            
            # Валидация
            val_output = self.forward(X_val)
            val_loss = -np.sum(y_val * np.log(val_output + 1e-12)) / len(X_val)
            val_acc = np.mean(np.argmax(val_output, axis=1) == np.argmax(y_val, axis=1))
            
            train_losses.append(epoch_loss)
            train_accs.append(epoch_acc)
            val_losses.append(val_loss)
            val_accs.append(val_acc)
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Train Loss={epoch_loss:.4f}, Train Acc={epoch_acc:.4f}, "
                      f"Val Loss={val_loss:.4f}, Val Acc={val_acc:.4f}")
        
        return train_losses, val_losses, train_accs, val_accs

# Обучение
print("Загрузка данных...")
nn = NeuralNetwork()

print("\nОбучение модели...")
history = nn.train(X_train, y_train, X_val, y_val, epochs=30)

# Графики
print("\nСтроим графики...")
train_loss, val_loss, train_acc, val_acc = history

plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_loss, 'b-', label='Train Loss', linewidth=2)
plt.plot(val_loss, 'r-', label='Val Loss', linewidth=2)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(train_acc, 'b-', label='Train Acc', linewidth=2)
plt.plot(val_acc, 'r-', label='Val Acc', linewidth=2)
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Accuracy')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('training_plots.png')
plt.show()

# Тест
print("\nТестирование...")
test_output = nn.forward(X_test)
test_acc = np.mean(np.argmax(test_output, axis=1) == np.argmax(y_test, axis=1))
print(f"Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")

# Примеры
print("\nПримеры предсказаний:")
for i in range(5):
    sample = X_test[i:i+1]
    true = np.argmax(y_test[i])
    pred = np.argmax(nn.forward(sample)[0])
    print(f"  Изображение {i}: True={true}, Pred={pred} {'✓' if true==pred else '✗'}")
