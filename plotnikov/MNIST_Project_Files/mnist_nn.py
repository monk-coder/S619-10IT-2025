pip install numpy matplotlibpip install numpy matplotlibpip install numpy matplotlibimport numpy as np
import matplotlib.pyplot as plt
import pickle
import os
from urllib import request
import gzip

class NeuralNetwork:
    """Нейронная сеть для классификации MNIST."""
    
    def __init__(self, layer_sizes, learning_rate=0.1, reg_lambda=0.001):
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.reg_lambda = reg_lambda
        self.num_layers = len(layer_sizes)
        
        # Инициализация весов
        self.weights = []
        self.biases = []
        
        for i in range(self.num_layers - 1):
            limit = np.sqrt(6 / (layer_sizes[i] + layer_sizes[i + 1]))
            W = np.random.uniform(-limit, limit, (layer_sizes[i], layer_sizes[i + 1]))
            b = np.zeros((1, layer_sizes[i + 1]))
            self.weights.append(W)
            self.biases.append(b)
        
        self.history = {'train_loss': [], 'train_acc': [], 'val_acc': []}
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def relu_derivative(self, x):
        return (x > 0).astype(float)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        """Прямое распространение."""
        activations = [X]
        zs = []
        
        # Скрытые слои с ReLU
        for i in range(self.num_layers - 2):
            z = activations[-1] @ self.weights[i] + self.biases[i]
            a = self.relu(z)
            zs.append(z)
            activations.append(a)
        
        # Выходной слой с Softmax
        z = activations[-1] @ self.weights[-1] + self.biases[-1]
        a = self.softmax(z)
        zs.append(z)
        activations.append(a)
        
        return activations, zs
    
    def compute_loss(self, y_pred, y_true):
        """Вычисление кросс-энтропии с L2 регуляризацией."""
        m = y_true.shape[0]
        
        # Кросс-энтропия
        y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
        cross_entropy = -np.sum(y_true * np.log(y_pred)) / m
        
        # L2 регуляризация
        l2_penalty = sum(np.sum(W ** 2) for W in self.weights)
        l2_penalty = (self.reg_lambda / (2 * m)) * l2_penalty
        
        return cross_entropy + l2_penalty
    
    def backward(self, X, y, activations, zs):
        """Обратное распространение."""
        m = X.shape[0]
        grad_w = []
        grad_b = []
        
        # Ошибка выходного слоя
        delta = activations[-1] - y
        
        # Градиенты для каждого слоя
        for l in range(self.num_layers - 2, -1, -1):
            # Градиенты весов и смещений
            g_w = activations[l].T @ delta / m + (self.reg_lambda / m) * self.weights[l]
            g_b = np.sum(delta, axis=0, keepdims=True) / m
            
            grad_w.insert(0, g_w)
            grad_b.insert(0, g_b)
            
            # Распространение ошибки на предыдущий слой
            if l > 0:
                delta = delta @ self.weights[l].T * self.relu_derivative(activations[l])
        
        return grad_w, grad_b
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=30, batch_size=64):
        """Обучение модели."""
        n = X_train.shape[0]
        
        for epoch in range(epochs):
            # Перемешивание данных
            idx = np.random.permutation(n)
            X_shuffled = X_train[idx]
            y_shuffled = y_train[idx]
            
            epoch_loss = 0
            correct = 0
            
            # Обучение по батчам
            for i in range(0, n, batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch = y_shuffled[i:i+batch_size]
                
                # Прямое распространение
                activations, zs = self.forward(X_batch)
                
                # Потери и точность
                batch_loss = self.compute_loss(activations[-1], y_batch)
                epoch_loss += batch_loss
                
                pred = np.argmax(activations[-1], axis=1)
                true = np.argmax(y_batch, axis=1)
                correct += np.sum(pred == true)
                
                # Обратное распространение и обновление
                grad_w, grad_b = self.backward(X_batch, y_batch, activations, zs)
                
                for j in range(len(self.weights)):
                    self.weights[j] -= self.learning_rate * grad_w[j]
                    self.biases[j] -= self.learning_rate * grad_b[j]
            
            # Статистика эпохи
            avg_loss = epoch_loss / (n // batch_size)
            acc = correct / n
            
            self.history['train_loss'].append(avg_loss)
            self.history['train_acc'].append(acc)
            
            # Валидация
            if X_val is not None:
                val_acc = self.accuracy(X_val, y_val)
                self.history['val_acc'].append(val_acc)
                print(f"Эпоха {epoch+1}/{epochs}: loss={avg_loss:.4f}, acc={acc:.4f}, val_acc={val_acc:.4f}")
            else:
                print(f"Эпоха {epoch+1}/{epochs}: loss={avg_loss:.4f}, acc={acc:.4f}")
    
    def predict(self, X):
        """Предсказание классов."""
        activations, _ = self.forward(X)
        probs = activations[-1]
        preds = np.argmax(probs, axis=1)
        return preds, probs
    
    def accuracy(self, X, y):
        """Вычисление точности."""
        preds, _ = self.predict(X)
        true = np.argmax(y, axis=1)
        return np.mean(preds == true)
    
    def evaluate(self, X, y):
        """Оценка модели."""
        activations, _ = self.forward(X)
        loss = self.compute_loss(activations[-1], y)
        acc = self.accuracy(X, y)
        return loss, acc
    
    def plot_history(self):
        """Построение графиков обучения."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        ax1.plot(self.history['train_loss'])
        ax1.set_xlabel('Эпоха')
        ax1.set_ylabel('Потери')
        ax1.set_title('Потери при обучении')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(self.history['train_acc'], label='Train')
        if self.history['val_acc']:
            ax2.plot(self.history['val_acc'], label='Validation')
        ax2.set_xlabel('Эпоха')
        ax2.set_ylabel('Точность')
        ax2.set_title('Точность при обучении')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('training_history.png', dpi=150, bbox_inches='tight')
        plt.show()
    
    def save(self, filename):
        """Сохранение модели."""
        data = {
            'weights': self.weights,
            'biases': self.biases,
            'layer_sizes': self.layer_sizes,
            'history': self.history
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f"Модель сохранена: {filename}")
    
    @classmethod
    def load(cls, filename):
        """Загрузка модели."""
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        model = cls(data['layer_sizes'])
        model.weights = data['weights']
        model.biases = data['biases']
        model.history = data['history']
        
        print(f"Модель загружена: {filename}")
        return model


def load_mnist():
    """Загрузка датасета MNIST."""
    # URLs для скачивания
    urls = {
        'train_images': 'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz',
        'train_labels': 'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz',
        'test_images': 'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz',
        'test_labels': 'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz'
    }
    
    def download_and_extract(url, filename):
        if not os.path.exists(filename):
            print(f"Скачивание {filename}...")
            request.urlretrieve(url, filename + '.gz')
            with gzip.open(filename + '.gz', 'rb') as f:
                with open(filename, 'wb') as out:
                    out.write(f.read())
            os.remove(filename + '.gz')
    
    # Создаем папку для данных
    os.makedirs('data', exist_ok=True)
    
    # Скачиваем файлы
    for name, url in urls.items():
        download_and_extract(url, f'data/{name}')
    
    # Загружаем данные
    def load_images(filename):
        with open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=16)
        return data.reshape(-1, 28*28).astype(np.float32) / 255.0
    
    def load_labels(filename):
        with open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=8)
        return data.astype(np.int32)
    
    # Загрузка всех данных
    X_train = load_images('data/train_images')
    y_train = load_labels('data/train_labels')
    X_test = load_images('data/test_images')
    y_test = load_labels('data/test_labels')
    
    # Преобразование в one-hot
    def to_onehot(y, num_classes=10):
        onehot = np.zeros((len(y), num_classes))
        onehot[np.arange(len(y)), y] = 1
        return onehot
    
    y_train_onehot = to_onehot(y_train)
    y_test_onehot = to_onehot(y_test)
    
    print(f"Данные загружены: {len(X_train)} train, {len(X_test)} test")
    return X_train, y_train_onehot, X_test, y_test_onehot, y_test


def create_validation(X, y, val_split=0.1):
    """Создание валидационного набора."""
    n = len(X)
    n_val = int(n * val_split)
    
    idx = np.random.permutation(n)
    val_idx = idx[:n_val]
    train_idx = idx[n_val:]
    
    return X[train_idx], y[train_idx], X[val_idx], y[val_idx]


def main():
    """Основная функция."""
    print("="*50)
    print("Нейронная сеть для MNIST")
    print("="*50)
    
    # Загрузка данных
    print("\n1. Загрузка MNIST...")
    data = load_mnist()
    if data is None:
        print("Ошибка загрузки данных!")
        return
    
    X_train, y_train, X_test, y_test, y_test_labels = data
    
    # Валидационный набор
    print("2. Создание валидационного набора...")
    X_train, y_train, X_val, y_val = create_validation(X_train, y_train, 0.1)
    
    print(f"   Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Создание модели
    print("3. Создание нейронной сети...")
    model = NeuralNetwork(
        layer_sizes=[784, 128, 64, 10],
        learning_rate=0.1,
        reg_lambda=0.001
    )
    
    # Обучение
    print("4. Обучение...")
    print("-"*40)
    model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=30,
        batch_size=64
    )
    
    # Тестирование
    print("\n5. Тестирование...")
    test_loss, test_acc = model.evaluate(X_test, y_test)
    print(f"   Test accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"   Test loss: {test_loss:.4f}")
    
    # Визуализация
    print("\n6. Визуализация...")
    model.plot_history()
    
    # Сохранение
    print("\n7. Сохранение модели...")
    model.save('mnist_model.pkl')
    
    # Примеры
    print("\n8. Примеры предсказаний:")
    for i in range(3):
        sample = X_test[i:i+1]
        pred, _ = model.predict(sample)
        true = y_test_labels[i]
        print(f"   Пример {i+1}: Истина={true}, Предсказание={pred[0]}")
    
    print("\n" + "="*50)
    print(f"Готово! Точность: {test_acc*100:.2f}%")
    print("="*50)


if __name__ == "__main__":
    main()