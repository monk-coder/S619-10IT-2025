import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import time

class NeuralNetwork:
    """Нейронная сеть для классификации MNIST"""
    
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        """
        Инициализация нейронной сети
        
        Параметры:
        - input_size: размер входного слоя (784 для MNIST)
        - hidden_size: размер скрытого слоя
        - output_size: размер выходного слоя (10 для цифр 0-9)
        - learning_rate: скорость обучения
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Инициализация весов с помощью Xavier/Glorot инициализации
        self.W1 = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((hidden_size, 1))
        
        self.W2 = np.random.randn(output_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((output_size, 1))
        
        # Хранение истории для графиков
        self.train_loss_history = []
        self.train_accuracy_history = []
        self.val_loss_history = []
        self.val_accuracy_history = []
    
    def sigmoid(self, x):
        """Сигмоидная функция активации"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def sigmoid_derivative(self, x):
        """Производная сигмоидной функции"""
        return x * (1 - x)
    
    def softmax(self, x):
        """Функция softmax для многоклассовой классификации"""
        exp_x = np.exp(x - np.max(x, axis=0, keepdims=True))
        return exp_x / np.sum(exp_x, axis=0, keepdims=True)
    
    def forward_propagation(self, X):
        """
        Прямое распространение
        
        Параметры:
        - X: входные данные (размер: features × samples)
        
        Возвращает:
        - z1, a1, z2, a2: значения на каждом слое
        """
        # Скрытый слой
        z1 = np.dot(self.W1, X) + self.b1
        a1 = self.sigmoid(z1)
        
        # Выходной слой
        z2 = np.dot(self.W2, a1) + self.b2
        a2 = self.softmax(z2)
        
        return z1, a1, z2, a2
    
    def compute_loss(self, y_true, y_pred):
        """
        Вычисление функции потерь (кросс-энтропия)
        
        Параметры:
        - y_true: истинные метки (one-hot encoded)
        - y_pred: предсказанные вероятности
        """
        m = y_true.shape[1]
        # Добавляем небольшое значение для избежания log(0)
        loss = -np.sum(y_true * np.log(y_pred + 1e-8)) / m
        return loss
    
    def compute_accuracy(self, y_true, y_pred):
        """
        Вычисление точности
        
        Параметры:
        - y_true: истинные метки (one-hot encoded или индексы)
        - y_pred: предсказанные вероятности или индексы
        """
        if y_true.ndim == 2:  # one-hot encoded
            y_true_indices = np.argmax(y_true, axis=0)
        else:
            y_true_indices = y_true
            
        if y_pred.ndim == 2:  # вероятности
            y_pred_indices = np.argmax(y_pred, axis=0)
        else:
            y_pred_indices = y_pred
            
        accuracy = np.mean(y_true_indices == y_pred_indices)
        return accuracy
    
    def backward_propagation(self, X, y, z1, a1, z2, a2):
        """
        Обратное распространение ошибки
        
        Параметры:
        - X: входные данные
        - y: истинные метки (one-hot encoded)
        - z1, a1, z2, a2: значения из forward propagation
        """
        m = X.shape[1]
        
        # Ошибка на выходном слое
        dz2 = a2 - y  # ∂L/∂z2
        dW2 = np.dot(dz2, a1.T) / m
        db2 = np.sum(dz2, axis=1, keepdims=True) / m
        
        # Ошибка на скрытом слое
        da1 = np.dot(self.W2.T, dz2)
        dz1 = da1 * self.sigmoid_derivative(a1)
        dW1 = np.dot(dz1, X.T) / m
        db1 = np.sum(dz1, axis=1, keepdims=True) / m
        
        return dW1, db1, dW2, db2
    
    def update_parameters(self, dW1, db1, dW2, db2):
        """
        Обновление параметров с помощью градиентного спуска
        """
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32, verbose=True):
        """
        Обучение нейронной сети
        
        Параметры:
        - X_train, y_train: тренировочные данные
        - X_val, y_val: валидационные данные
        - epochs: количество эпох
        - batch_size: размер батча
        - verbose: вывод прогресса
        """
        n_samples = X_train.shape[1]
        
        print(f"Начало обучения...")
        print(f"Размер тренировочной выборки: {n_samples}")
        print(f"Размер валидационной выборки: {X_val.shape[1]}")
        print(f"Эпохи: {epochs}, Размер батча: {batch_size}")
        print("-" * 50)
        
        start_time = time.time()
        
        for epoch in range(epochs):
            # Перемешивание данных
            permutation = np.random.permutation(n_samples)
            X_shuffled = X_train[:, permutation]
            y_shuffled = y_train[:, permutation]
            
            epoch_loss = 0
            epoch_accuracy = 0
            
            # Мини-батчи
            for i in range(0, n_samples, batch_size):
                # Получение батча
                end_idx = min(i + batch_size, n_samples)
                X_batch = X_shuffled[:, i:end_idx]
                y_batch = y_shuffled[:, i:end_idx]
                
                # Прямое распространение
                z1, a1, z2, a2 = self.forward_propagation(X_batch)
                
                # Вычисление потерь и точности
                batch_loss = self.compute_loss(y_batch, a2)
                batch_accuracy = self.compute_accuracy(y_batch, a2)
                
                epoch_loss += batch_loss * (end_idx - i)
                epoch_accuracy += batch_accuracy * (end_idx - i)
                
                # Обратное распространение
                dW1, db1, dW2, db2 = self.backward_propagation(X_batch, y_batch, z1, a1, z2, a2)
                
                # Обновление параметров
                self.update_parameters(dW1, db1, dW2, db2)
            
            # Средние значения по эпохе
            epoch_loss /= n_samples
            epoch_accuracy /= n_samples
            
            # Валидация
            val_z1, val_a1, val_z2, val_a2 = self.forward_propagation(X_val)
            val_loss = self.compute_loss(y_val, val_a2)
            val_accuracy = self.compute_accuracy(y_val, val_a2)
            
            # Сохранение истории
            self.train_loss_history.append(epoch_loss)
            self.train_accuracy_history.append(epoch_accuracy)
            self.val_loss_history.append(val_loss)
            self.val_accuracy_history.append(val_accuracy)
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Эпоха {epoch + 1}/{epochs}")
                print(f"  Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_accuracy:.4f}")
                print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")
                print("-" * 40)
        
        training_time = time.time() - start_time
        print(f"\nОбучение завершено за {training_time:.2f} секунд")
        print(f"Финальная точность на валидации: {self.val_accuracy_history[-1]:.4f}")
    
    def predict(self, X):
        """
        Предсказание для новых данных
        """
        _, _, _, a2 = self.forward_propagation(X)
        predictions = np.argmax(a2, axis=0)
        return predictions
    
    def plot_training_history(self, save_path=None):
        """
        Построение графиков обучения
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # График потерь
        ax1.plot(self.train_loss_history, label='Train Loss')
        ax1.plot(self.val_loss_history, label='Validation Loss')
        ax1.set_xlabel('Эпохи')
        ax1.set_ylabel('Loss')
        ax1.set_title('Функция потерь во время обучения')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График точности
        ax2.plot(self.train_accuracy_history, label='Train Accuracy')
        ax2.plot(self.val_accuracy_history, label='Validation Accuracy')
        ax2.set_xlabel('Эпохи')
        ax2.set_ylabel('Accuracy')
        ax2.set_title('Точность во время обучения')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()


def load_and_prepare_mnist(n_samples=10000):
    """
    Загрузка и подготовка данных MNIST
    
    Параметры:
    - n_samples: количество образцов для загрузки
    """
    print("Загрузка данных MNIST...")
    
    # Загрузка данных MNIST из OpenML
    mnist = fetch_openml('mnist_784', version=1, parser='auto')
    X = mnist.data.values
    y = mnist.target.values.astype(int)
    
    # Ограничение количества образцов для более быстрой тренировки
    if n_samples < len(X):
        indices = np.random.choice(len(X), n_samples, replace=False)
        X = X[indices]
        y = y[indices]
    
    # Нормализация пикселей в диапазон [0, 1]
    X = X.astype(np.float32) / 255.0
    
    # One-hot encoding для меток
    encoder = OneHotEncoder(sparse_output=False, categories=[range(10)])
    y_onehot = encoder.fit_transform(y.reshape(-1, 1)).T
    
    # Транспонирование для формата (features × samples)
    X = X.T
    
    # Разделение на тренировочную и тестовую выборки
    X_train, X_temp, y_train, y_temp = train_test_split(
        X.T, y_onehot.T, test_size=0.3, random_state=42, stratify=y
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y[:len(X_temp)]
    )
    
    # Возвращаем в формате (features × samples)
    return (
        X_train.T, y_train.T,
        X_val.T, y_val.T,
        X_test.T, y_test.T,
        y[:len(X_train)], y[len(X_train):len(X_train)+len(X_val)], y[len(X_train)+len(X_val):]
    )


def evaluate_model(model, X_test, y_test, y_test_labels):
    """
    Оценка модели на тестовой выборке
    """
    print("\n" + "="*50)
    print("ОЦЕНКА НА ТЕСТОВОЙ ВЫБОРКЕ")
    print("="*50)
    
    # Предсказания
    predictions = model.predict(X_test)
    
    # Точность
    test_accuracy = model.compute_accuracy(y_test_labels, predictions)
    print(f"Точность на тестовой выборке: {test_accuracy:.4f}")
    
    # Матрица ошибок
    from sklearn.metrics import confusion_matrix, classification_report
    cm = confusion_matrix(y_test_labels, predictions)
    
    print("\nМатрица ошибок:")
    print(cm)
    
    print("\nОтчет по классификации:")
    print(classification_report(y_test_labels, predictions, digits=4))
    
    # Визуализация нескольких примеров
    visualize_predictions(model, X_test, y_test_labels, predictions, n_samples=10)


def visualize_predictions(model, X, y_true, y_pred, n_samples=10):
    """
    Визуализация предсказаний модели
    """
    fig, axes = plt.subplots(2, 5, figsize=(12, 5))
    axes = axes.flatten()
    
    indices = np.random.choice(X.shape[1], n_samples, replace=False)
    
    for idx, ax in enumerate(axes):
        if idx < len(indices):
            sample_idx = indices[idx]
            image = X[:, sample_idx].reshape(28, 28)
            true_label = y_true[sample_idx]
            pred_label = y_pred[sample_idx]
            
            ax.imshow(image, cmap='gray')
            ax.set_title(f"True: {true_label}\nPred: {pred_label}")
            ax.axis('off')
            
            # Подсветка неверных предсказаний
            if true_label != pred_label:
                ax.spines['bottom'].set_color('red')
                ax.spines['top'].set_color('red')
                ax.spines['left'].set_color('red')
                ax.spines['right'].set_color('red')
                ax.spines['bottom'].set_linewidth(2)
                ax.spines['top'].set_linewidth(2)
                ax.spines['left'].set_linewidth(2)
                ax.spines['right'].set_linewidth(2)
    
    plt.suptitle("Примеры предсказаний модели (красная рамка = ошибка)", fontsize=12)
    plt.tight_layout()
    plt.show()


def main():
    """Основная функция для запуска обучения и оценки"""
    
    # Загрузка данных
    X_train, y_train_onehot, X_val, y_val_onehot, X_test, y_test_onehot, \
    y_train_labels, y_val_labels, y_test_labels = load_and_prepare_mnist(n_samples=20000)
    
    print(f"\nРазмерности данных:")
    print(f"X_train: {X_train.shape}")
    print(f"y_train: {y_train_onehot.shape}")
    print(f"X_val: {X_val.shape}")
    print(f"X_test: {X_test.shape}")
    
    # Создание и обучение модели
    input_size = 784  # 28x28 пикселей
    hidden_size = 128  # нейронов в скрытом слое
    output_size = 10   # цифры 0-9
    
    # Можно экспериментировать с гиперпараметрами
    hyperparameters = [
        {'learning_rate': 0.1, 'epochs': 50, 'batch_size': 32},
        {'learning_rate': 0.05, 'epochs': 50, 'batch_size': 64},
        {'learning_rate': 0.01, 'epochs': 100, 'batch_size': 128},
    ]
    
    best_accuracy = 0
    best_model = None
    best_params = None
    
    for i, params in enumerate(hyperparameters):
        print(f"\n{'='*60}")
        print(f"Эксперимент {i+1}: LR={params['learning_rate']}, "
              f"Epochs={params['epochs']}, Batch={params['batch_size']}")
        print('='*60)
        
        # Создание модели
        model = NeuralNetwork(
            input_size=input_size,
            hidden_size=hidden_size,
            output_size=output_size,
            learning_rate=params['learning_rate']
        )
        
        # Обучение
        model.train(
            X_train=X_train,
            y_train=y_train_onehot,
            X_val=X_val,
            y_val=y_val_onehot,
            epochs=params['epochs'],
            batch_size=params['batch_size'],
            verbose=True
        )
        
        # Оценка на валидации
        val_accuracy = model.val_accuracy_history[-1]
        
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_model = model
            best_params = params
        
        # Построение графиков для этого эксперимента
        model.plot_training_history(save_path=f'plots/experiment_{i+1}.png')
    
    print(f"\n{'='*60}")
    print(f"ЛУЧШАЯ МОДЕЛЬ:")
    print(f"Параметры: {best_params}")
    print(f"Точность на валидации: {best_accuracy:.4f}")
    print('='*60)
    
    # Оценка лучшей модели на тестовой выборке
    evaluate_model(best_model, X_test, y_test_onehot, y_test_labels)
    
    return best_model


if __name__ == "__main__":
    # Создание папки для графиков
    import os
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    # Запуск
    model = main()