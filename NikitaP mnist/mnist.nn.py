import numpy as np
import urllib.request
import gzip
import os
import struct
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

print("="*70)
print("НЕЙРОННАЯ СЕТЬ ДЛЯ MNIST - ПОЛНЫЙ ГРАФИК")
print("="*70)

# ==================== ЗАГРУЗКА РЕАЛЬНОГО MNIST ====================
def load_mnist():
    """Загрузка реального датасета MNIST"""
    print("\n📥 Загрузка датасета MNIST...")
    
    urls = [
        ('train-images-idx3-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz'),
        ('train-labels-idx1-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz'),
        ('t10k-images-idx3-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz'),
        ('t10k-labels-idx1-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz')
    ]
    
    for filename, url in urls:
        if not os.path.exists(filename):
            print(f"Скачивание {filename}...")
            urllib.request.urlretrieve(url, filename)
    
    def read_mnist_images(filename):
        with gzip.open(filename, 'rb') as f:
            magic, num, rows, cols = struct.unpack(">IIII", f.read(16))
            images = np.frombuffer(f.read(), dtype=np.uint8)
            images = images.reshape(num, rows * cols).astype('float32') / 255.0
            return images
    
    def read_mnist_labels(filename):
        with gzip.open(filename, 'rb') as f:
            magic, num = struct.unpack(">II", f.read(8))
            labels = np.frombuffer(f.read(), dtype=np.uint8)
            return labels
    
    X_train = read_mnist_images('train-images-idx3-ubyte.gz')
    y_train = read_mnist_labels('train-labels-idx1-ubyte.gz')
    X_test = read_mnist_images('t10k-images-idx3-ubyte.gz')
    y_test = read_mnist_labels('t10k-labels-idx1-ubyte.gz')
    
    print(f"✅ Загружено: {len(X_train)} тренировочных и {len(X_test)} тестовых изображений")
    return X_train, y_train, X_test, y_test

# Загружаем данные
X_train, y_train, X_test, y_test = load_mnist()

def one_hot_encode(y, num_classes=10):
    y_onehot = np.zeros((len(y), num_classes))
    y_onehot[np.arange(len(y)), y] = 1
    return y_onehot

y_train_onehot = one_hot_encode(y_train)
y_test_onehot = one_hot_encode(y_test)

val_size = 10000
X_val, y_val = X_train[:val_size], y_train_onehot[:val_size]
X_train, y_train = X_train[val_size:], y_train_onehot[val_size:]

print(f"\n📊 Размеры данных:")
print(f"  Train: {X_train.shape[0]} | Val: {X_val.shape[0]} | Test: {X_test.shape[0]}")

# ==================== НЕЙРОННАЯ СЕТЬ ====================
class NeuralNetwork:
    def __init__(self):
        np.random.seed(42)
        
        self.W1 = np.random.randn(784, 256) * np.sqrt(2.0 / 784)
        self.b1 = np.zeros((1, 256))
        
        self.W2 = np.random.randn(256, 128) * np.sqrt(2.0 / 256)
        self.b2 = np.zeros((1, 128))
        
        self.W3 = np.random.randn(128, 10) * np.sqrt(2.0 / 128)
        self.b3 = np.zeros((1, 10))
        
        self.lr = 0.01
        self.lr_decay = 0.97
        self.momentum = 0.9
        
        self.vW1 = np.zeros_like(self.W1)
        self.vW2 = np.zeros_like(self.W2)
        self.vW3 = np.zeros_like(self.W3)
        self.vb1 = np.zeros_like(self.b1)
        self.vb2 = np.zeros_like(self.b2)
        self.vb3 = np.zeros_like(self.b3)
        
        self.history = {
            'train_loss': [], 'train_acc': [],
            'val_loss': [], 'val_acc': []
        }
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def relu_deriv(self, x):
        return (x > 0).astype(float)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        self.A0 = X
        self.Z1 = X @ self.W1 + self.b1
        self.A1 = self.relu(self.Z1)
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = self.relu(self.Z2)
        self.Z3 = self.A2 @ self.W3 + self.b3
        return self.softmax(self.Z3)
    
    def backward(self, X, y_true):
        m = X.shape[0]
        y_pred = self.forward(X)
        
        dZ3 = y_pred - y_true
        dW3 = self.A2.T @ dZ3 / m
        db3 = np.sum(dZ3, axis=0, keepdims=True) / m
        
        dA2 = dZ3 @ self.W3.T
        dZ2 = dA2 * self.relu_deriv(self.Z2)
        dW2 = self.A1.T @ dZ2 / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m
        
        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * self.relu_deriv(self.Z1)
        dW1 = self.A0.T @ dZ1 / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m
        
        self.vW3 = self.momentum * self.vW3 + self.lr * dW3
        self.vb3 = self.momentum * self.vb3 + self.lr * db3
        self.vW2 = self.momentum * self.vW2 + self.lr * dW2
        self.vb2 = self.momentum * self.vb2 + self.lr * db2
        self.vW1 = self.momentum * self.vW1 + self.lr * dW1
        self.vb1 = self.momentum * self.vb1 + self.lr * db1
        
        self.W3 -= self.vW3
        self.b3 -= self.vb3
        self.W2 -= self.vW2
        self.b2 -= self.vb2
        self.W1 -= self.vW1
        self.b1 -= self.vb1
        
        loss = -np.sum(y_true * np.log(y_pred + 1e-12)) / m
        acc = np.mean(np.argmax(y_pred, axis=1) == np.argmax(y_true, axis=1))
        
        return loss, acc
    
    def decay_learning_rate(self):
        self.lr *= self.lr_decay
    
    def train(self, X_train, y_train, X_val, y_val, epochs=30, batch_size=128):
        print("\n" + "="*60)
        print("ОБУЧЕНИЕ НЕЙРОННОЙ СЕТИ")
        print("="*60)
        
        print(f"Архитектура: 784 → 256 → 128 → 10")
        print(f"Learning rate: {self.lr}")
        print(f"Momentum: {self.momentum}")
        print(f"Batch size: {batch_size}")
        print(f"Epochs: {epochs}")
        print("-" * 60)
        
        best_val_acc = 0
        
        for epoch in range(epochs):
            idx = np.random.permutation(len(X_train))
            X_shuffled, y_shuffled = X_train[idx], y_train[idx]
            
            epoch_loss, epoch_acc = 0, 0
            
            for i in range(0, len(X_train), batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                loss, acc = self.backward(X_batch, y_batch)
                epoch_loss += loss * len(X_batch)
                epoch_acc += acc * len(X_batch)
            
            epoch_loss /= len(X_train)
            epoch_acc /= len(X_train)
            
            val_pred = self.forward(X_val)
            val_loss = -np.sum(y_val * np.log(val_pred + 1e-12)) / len(X_val)
            val_acc = np.mean(np.argmax(val_pred, axis=1) == np.argmax(y_val, axis=1))
            
            self.history['train_loss'].append(epoch_loss)
            self.history['train_acc'].append(epoch_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
            
            if epoch > 10 and epoch % 5 == 0:
                self.decay_learning_rate()
            
            if epoch % 5 == 0 or epoch == epochs - 1:
                print(f"Эпоха {epoch:3d}: Loss={epoch_loss:.4f}, Acc={epoch_acc:.4f}, "
                      f"Val Loss={val_loss:.4f}, Val Acc={val_acc:.4f}")
        
        print(f"\n✅ Лучшая точность на валидации: {best_val_acc:.4f}")
        return best_val_acc
    
    def predict(self, X):
        y_pred = self.forward(X)
        return np.argmax(y_pred, axis=1)

# ==================== ОБУЧЕНИЕ ====================
model = NeuralNetwork()
best_val_acc = model.train(X_train, y_train, X_val, y_val, epochs=30, batch_size=128)

# ==================== ТЕСТИРОВАНИЕ ====================
print("\n" + "="*60)
print("ТЕСТИРОВАНИЕ")
print("="*60)

test_predictions = model.predict(X_test)
test_true = y_test
test_accuracy = np.mean(test_predictions == test_true)

print(f"\n📊 Тестовая точность: {test_accuracy:.4f} ({test_accuracy*100:.1f}%)")

# Статистика по классам
class_accuracies = {}
print("\n📈 Точность по классам:")
for digit in range(10):
    mask = (test_true == digit)
    if np.any(mask):
        correct = np.sum(test_predictions[mask] == digit)
        total = np.sum(mask)
        accuracy = correct / total
        class_accuracies[digit] = accuracy
        print(f"  Цифра {digit}: {correct:4d}/{total:4d} ({accuracy:.1%})")

# Матрица ошибок
confusion_matrix = np.zeros((10, 10), dtype=int)
for true, pred in zip(test_true, test_predictions):
    confusion_matrix[true, pred] += 1

# ==================== НОРМАЛЬНЫЙ ГРАФИК ====================
print("\n🎨 Построение графиков...")

plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(20, 12))
fig.patch.set_facecolor('#f8f9fa')

# 1. График потерь и точности
ax1 = plt.subplot(2, 3, 1)
ax1.plot(model.history['train_loss'], 'b-', linewidth=2.5, label='Обучающая', alpha=0.8)
ax1.plot(model.history['val_loss'], 'r-', linewidth=2.5, label='Валидационная', alpha=0.8)
ax1.set_xlabel('Эпоха', fontsize=11, fontweight='bold')
ax1.set_ylabel('Потери (Loss)', fontsize=11, fontweight='bold')
ax1.set_title('Функция потерь во время обучения', fontsize=12, fontweight='bold', pad=15)
ax1.legend(fontsize=10, loc='upper right')
ax1.grid(True, alpha=0.4)
ax1.set_facecolor('#ffffff')

ax2 = plt.subplot(2, 3, 2)
ax2.plot(model.history['train_acc'], 'b-', linewidth=2.5, label='Обучающая', alpha=0.8)
ax2.plot(model.history['val_acc'], 'r-', linewidth=2.5, label='Валидационная', alpha=0.8)
ax2.axhline(y=0.6, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Порог 60%')
ax2.fill_between(range(len(model.history['val_acc'])), 
                  0.6, model.history['val_acc'], 
                  where=(np.array(model.history['val_acc']) > 0.6),
                  color='green', alpha=0.2)
ax2.set_xlabel('Эпоха', fontsize=11, fontweight='bold')
ax2.set_ylabel('Точность (Accuracy)', fontsize=11, fontweight='bold')
ax2.set_title('Точность во время обучения', fontsize=12, fontweight='bold', pad=15)
ax2.legend(fontsize=10, loc='lower right')
ax2.grid(True, alpha=0.4)
ax2.set_ylim(0, 1)
ax2.set_facecolor('#ffffff')

# 2. Точность по классам (гистограмма)
ax3 = plt.subplot(2, 3, 3)
digits = list(class_accuracies.keys())
accuracies = [class_accuracies[d] for d in digits]
colors = plt.cm.viridis(np.linspace(0, 1, len(digits)))

bars = ax3.bar(digits, accuracies, color=colors, edgecolor='black', linewidth=1.2)
ax3.axhline(y=0.6, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Порог 60%')

for i, (bar, acc) in enumerate(zip(bars, accuracies)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{acc:.1%}', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax3.set_xlabel('Цифра', fontsize=11, fontweight='bold')
ax3.set_ylabel('Точность', fontsize=11, fontweight='bold')
ax3.set_title('Точность по классам цифр', fontsize=12, fontweight='bold', pad=15)
ax3.set_xticks(digits)
ax3.set_ylim(0, 1.05)
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.4, axis='y')
ax3.set_facecolor('#ffffff')

# 3. Матрица ошибок (heatmap)
ax4 = plt.subplot(2, 3, 4)
norm_matrix = confusion_matrix.astype('float') / confusion_matrix.sum(axis=1)[:, np.newaxis]
im = ax4.imshow(norm_matrix, cmap='YlOrRd', vmin=0, vmax=1)

# Добавляем текст в ячейки
for i in range(10):
    for j in range(10):
        color = 'white' if norm_matrix[i, j] > 0.5 else 'black'
        ax4.text(j, i, f'{confusion_matrix[i, j]:d}\n({norm_matrix[i, j]:.1%})',
                 ha='center', va='center', color=color, fontsize=8,
                 fontweight='bold' if i == j else 'normal')

ax4.set_xlabel('Предсказанная цифра', fontsize=11, fontweight='bold')
ax4.set_ylabel('Истинная цифра', fontsize=11, fontweight='bold')
ax4.set_title('Матрица ошибок', fontsize=12, fontweight='bold', pad=15)
ax4.set_xticks(range(10))
ax4.set_yticks(range(10))
ax4.set_facecolor('#ffffff')

# Добавляем рамку вокруг диагонали
for i in range(10):
    rect = Rectangle((i-0.5, i-0.5), 1, 1, linewidth=2, edgecolor='blue', facecolor='none', alpha=0.5)
    ax4.add_patch(rect)

# 4. Примеры изображений с предсказаниями
ax5 = plt.subplot(2, 3, 5)
ax5.axis('off')

# Находим примеры для каждого класса (правильные и ошибки)
correct_examples = []
incorrect_examples = []

for digit in range(10):
    mask_correct = (test_true == digit) & (test_predictions == digit)
    mask_incorrect = (test_true == digit) & (test_predictions != digit)
    
    if np.any(mask_correct):
        idx = np.where(mask_correct)[0][0]
        correct_examples.append((X_test[idx], digit, test_predictions[idx]))
    
    if np.any(mask_incorrect):
        idx = np.where(mask_incorrect)[0][0]
        incorrect_examples.append((X_test[idx], digit, test_predictions[idx]))

# Показываем по 5 примеров
text_content = "Примеры предсказаний:\n\n"
text_content += "✅ Правильные:\n"
for i, (img, true, pred) in enumerate(correct_examples[:5]):
    text_content += f"  Цифра {true} → {pred}\n"

text_content += "\n❌ Ошибки:\n"
for i, (img, true, pred) in enumerate(incorrect_examples[:5]):
    text_content += f"  Цифра {true} → {pred}\n"

text_content += f"\n📊 Итоговая точность: {test_accuracy:.2%}"

ax5.text(0.1, 0.95, text_content, transform=ax5.transAxes,
         fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

# 5. Архитектура сети
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

network_info = """
Архитектура нейронной сети:

╔══════════════════════════════════╗
║         784 (вход)               ║
║             ↓                    ║
║   Полносвязный слой              ║
║         784 → 256                ║
║       Активация: ReLU            ║
║             ↓                    ║
║   Полносвязный слой              ║
║         256 → 128                ║
║       Активация: ReLU            ║
║             ↓                    ║
║   Выходной слой                  ║
║         128 → 10                 ║
║     Активация: Softmax           ║
╚══════════════════════════════════╝

Параметры:
• Learning rate: 0.01
• Momentum: 0.9
• Batch size: 128
• Эпохи: 30
• Параметры: 269,322
• Точность: {:.1%}
""".format(test_accuracy)

ax6.text(0.1, 0.95, network_info, transform=ax6.transAxes,
         fontfamily='monospace', fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# Общий заголовок
plt.suptitle(f'Нейронная сеть для классификации MNIST\n'
             f'Финальная точность: {test_accuracy:.2%} | Эпохи: 30 | Архитектура: 784→256→128→10',
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('mnist_complete_report.png', dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
print("✅ Полный отчет сохранен в 'mnist_complete_report.png'")
plt.show()

# ==================== ИТОГ ====================
print("\n" + "="*70)
print("ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ")
print("="*70)

requirements = [
    ("Загрузка реального датасета MNIST", "✅"),
    ("Реализация Forward Propagation", "✅"),
    ("Реализация Backward Propagation", "✅"),
    ("Градиентный спуск с Momentum", "✅"),
    ("Обучение нейронной сети", "✅"),
    ("Оценка производительности", "✅"),
    ("Графики обучения (loss/accuracy)", "✅"),
    ("Точность >60%", "✅" if test_accuracy >= 0.6 else "❌")
]

for req, status in requirements:
    print(f"{status} {req}")

print("\n" + "="*70)
if test_accuracy >= 0.6:
    print(f"🎉 ЗАДАНИЕ ВЫПОЛНЕНО УСПЕШНО!")
    print(f"   Точность: {test_accuracy:.1%} (>60% ✓)")
else:
    print(f"⚠️  ВНИМАНИЕ: Точность ниже 60%")
    print(f"   Точность: {test_accuracy:.1%} (<60% ✗)")

print("="*70)
print("\n📁 Графики сохранены в:")
print("   - mnist_complete_report.png (полный отчет)")
print("\n⚙️  Для запуска требуется:")
print("   pip install numpy matplotlib")
