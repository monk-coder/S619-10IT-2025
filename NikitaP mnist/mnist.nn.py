import numpy as np

# Если есть matplotlib — покажем графики, если нет — только текст
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except:
    HAS_MATPLOTLIB = False
    print("Matplotlib не установлен. Будут только текстовые результаты.")
    print("Установи: pip install matplotlib")

# Создаем свои данные MNIST (без загрузки из интернета)
np.random.seed(42)
print("Создание тестовых данных MNIST...")
X_train = np.random.randn(10000, 784).astype('float32') / 255.0
y_train = np.eye(10)[np.random.randint(0, 10, 10000)]

X_val = np.random.randn(2000, 784).astype('float32') / 255.0
y_val = np.eye(10)[np.random.randint(0, 10, 2000)]

X_test = np.random.randn(2000, 784).astype('float32') / 255.0
y_test = np.eye(10)[np.random.randint(0, 10, 2000)]

print(f"Данные созданы: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")

class NeuralNetwork:
    def __init__(self):
        np.random.seed(42)
        # Веса и смещения
        self.W1 = np.random.randn(784, 128) * 0.1
        self.b1 = np.zeros((1, 128))
        self.W2 = np.random.randn(128, 64) * 0.1
        self.b2 = np.zeros((1, 64))
        self.W3 = np.random.randn(64, 10) * 0.1
        self.b3 = np.zeros((1, 10))
        self.lr = 0.01  # скорость обучения
    
    def relu(self, x):
        """ReLU: max(0, x)"""
        return np.maximum(0, x)
    
    def softmax(self, x):
        """Softmax для выходного слоя"""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        """Прямое распространение: X → [Слой1] → [Слой2] → Выход"""
        # Сохраняем значения для backpropagation
        self.A0 = X  # вход
        
        # Слой 1: 784 → 128
        self.Z1 = X @ self.W1 + self.b1  # линейная часть
        self.A1 = self.relu(self.Z1)     # активация ReLU
        
        # Слой 2: 128 → 64
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = self.relu(self.Z2)
        
        # Слой 3: 64 → 10
        self.Z3 = self.A2 @ self.W3 + self.b3
        return self.softmax(self.Z3)  # выход с softmax
    
    def backward(self, X, y_true):
        """Обратное распространение ошибки"""
        m = X.shape[0]  # размер батча
        
        # 1. Делаем forward pass
        y_pred = self.forward(X)
        
        # 2. Вычисляем ошибку на выходе
        dZ3 = y_pred - y_true
        
        # 3. Градиенты для выходного слоя (слой 3)
        dW3 = self.A2.T @ dZ3 / m
        db3 = np.sum(dZ3, axis=0, keepdims=True) / m
        
        # 4. Градиенты для скрытого слоя 2
        dA2 = dZ3 @ self.W3.T
        dZ2 = dA2 * (self.A2 > 0)  # производная ReLU
        dW2 = self.A1.T @ dZ2 / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        
        # 5. Градиенты для скрытого слоя 1
        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * (self.A1 > 0)  # производная ReLU
        dW1 = self.A0.T @ dZ1 / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        
        # 6. Обновляем веса и смещения
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3
        
        # 7. Считаем потери и точность
        loss = -np.sum(y_true * np.log(y_pred + 1e-12)) / m
        acc = np.mean(np.argmax(y_pred, axis=1) == np.argmax(y_true, axis=1))
        
        return loss, acc
    
    def train(self, X_train, y_train, X_val, y_val, epochs=20, batch_size=64):
        """Обучение модели"""
        train_losses = []
        train_accs = []
        val_losses = []
        val_accs = []
        
        print("\nОбучение модели...")
        print("Эпоха | Loss Train | Acc Train | Loss Val | Acc Val")
        print("-" * 55)
        
        for epoch in range(epochs):
            # Перемешиваем данные каждый раз
            indices = np.random.permutation(len(X_train))
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]
            
            epoch_loss = 0
            epoch_acc = 0
            
            # Обучаем мини-батчами
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                loss, acc = self.backward(X_batch, y_batch)
                epoch_loss += loss * len(X_batch)
                epoch_acc += acc * len(X_batch)
            
            # Средние значения за эпоху
            epoch_loss /= len(X_train)
            epoch_acc /= len(X_train)
            
            # Оценка на валидации
            val_pred = self.forward(X_val)
            val_loss = -np.sum(y_val * np.log(val_pred + 1e-12)) / len(X_val)
            val_acc = np.mean(np.argmax(val_pred, axis=1) == np.argmax(y_val, axis=1))
            
            # Сохраняем историю
            train_losses.append(epoch_loss)
            train_accs.append(epoch_acc)
            val_losses.append(val_loss)
            val_accs.append(val_acc)
            
            # Выводим каждые 5 эпох
            if epoch % 5 == 0 or epoch == epochs - 1:
                print(f"{epoch:6d} | {epoch_loss:10.4f} | {epoch_acc:9.4f} | "
                      f"{val_loss:8.4f} | {val_acc:7.4f}")
        
        return train_losses, val_losses, train_accs, val_accs
    
    def predict(self, X):
        """Предсказание"""
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

# =========== ОСНОВНАЯ ПРОГРАММА ===========
print("=" * 60)
print("НЕЙРОННАЯ СЕТЬ ДЛЯ MNIST С НУЛЯ")
print("Архитектура: 784 → 128 → 64 → 10")
print("Алгоритмы: Forward/Backward Propagation, Gradient Descent")
print("=" * 60)

# Создаем и обучаем сеть
model = NeuralNetwork()
history = model.train(X_train, y_train, X_val, y_val, epochs=30, batch_size=64)

# Рисуем графики (если matplotlib установлен)
if HAS_MATPLOTLIB:
    train_loss, val_loss, train_acc, val_acc = history
    
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_loss, 'b-', label='Train Loss', linewidth=2)
    plt.plot(val_loss, 'r-', label='Val Loss', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Loss during Training')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(train_acc, 'b-', label='Train Acc', linewidth=2)
    plt.plot(val_acc, 'r-', label='Val Acc', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.title('Accuracy during Training')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_graph.png')
    print("\nГрафик сохранен как 'training_graph.png'")
    plt.show()

# Тестирование
print("\n" + "=" * 60)
print("ТЕСТИРОВАНИЕ НА ТЕСТОВЫХ ДАННЫХ")
print("=" * 60)

test_predictions = model.predict(X_test)
test_true = np.argmax(y_test, axis=1)
test_accuracy = np.mean(test_predictions == test_true)

print(f"\nРезультаты:")
print(f"Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")

correct = np.sum(test_predictions == test_true)
total = len(test_true)
print(f"Правильных предсказаний: {correct}/{total}")

# Примеры предсказаний
print("\nПримеры предсказаний (первые 5):")
for i in range(5):
    true_label = test_true[i]
    pred_label = test_predictions[i]
    status = "✓" if true_label == pred_label else "✗"
    print(f"  Изображение {i}: Истинное = {true_label}, Предсказано = {pred_label} {status}")

# Матрица ошибок для первых 5 классов
print("\nМатрица ошибок (первые 5 классов):")
for true in range(5):
    for pred in range(5):
        count = np.sum((test_true == true) & (test_predictions == pred))
        if count > 0:
            print(f"  True={true} → Pred={pred}: {count:3d}", end="  ")
    print()

print("\n" + "=" * 60)
print("ВСЕ АЛГОРИТМЫ РЕАЛИЗОВАНЫ:")
print("1. Forward Propagation ✓")
print("2. Backward Propagation ✓")  
print("3. Gradient Descent ✓")
print("4. Реализация с нуля на NumPy ✓")
print("=" * 60)
