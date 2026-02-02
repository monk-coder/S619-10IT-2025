import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
import time
import warnings

warnings.filterwarnings('ignore')


# Загрузка и подготовка данных
def load_mnist_data():
    """Загрузка и подготовка данных MNIST"""
    print("Загрузка данных MNIST...")
    mnist = fetch_openml('mnist_784', version=1, parser='auto')
    X = mnist.data.astype('float32')
    y = mnist.target.astype('int32')

    # Нормализация пикселей в диапазон [0, 1]
    X = X / 255.0

    # One-hot кодирование меток
    lb = LabelBinarizer()
    y_one_hot = lb.fit_transform(y)

    # Разделение на тренировочную и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_one_hot, test_size=0.2, random_state=42
    )

    print(f"Данные загружены:")
    print(f"  Обучающая выборка: {X_train.shape[0]} изображений")
    print(f"  Тестовая выборка: {X_test.shape[0]} изображений")
    print(f"  Размер изображения: {X_train.shape[1]} пикселей")

    return X_train, X_test, y_train, y_test, y


# Класс нейронной сети
class NeuralNetwork:
    def __init__(self, layer_sizes, learning_rate=0.1, reg_lambda=0.01):
        """
        Инициализация нейронной сети

        Parameters:
        -----------
        layer_sizes : list
            Список размеров слоев (входной, скрытые, выходной)
        learning_rate : float
            Скорость обучения
        reg_lambda : float
            Параметр регуляризации L2
        """
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.reg_lambda = reg_lambda
        self.parameters = {}
        self.history = {'loss': [], 'accuracy': [], 'val_loss': [], 'val_accuracy': []}

        # Инициализация параметров
        self._initialize_parameters()

    def _initialize_parameters(self):
        """Инициализация весов и смещений"""
        np.random.seed(42)

        for i in range(1, len(self.layer_sizes)):
            # Инициализация весов методом Xavier/Glorot
            scale = np.sqrt(2.0 / self.layer_sizes[i - 1])
            self.parameters[f'W{i}'] = np.random.randn(
                self.layer_sizes[i], self.layer_sizes[i - 1]
            ) * scale

            # Инициализация смещений нулями
            self.parameters[f'b{i}'] = np.zeros((self.layer_sizes[i], 1))

    def _sigmoid(self, z):
        """Сигмоидная функция активации"""
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def _sigmoid_derivative(self, a):
        """Производная сигмоидной функции"""
        return a * (1 - a)

    def _relu(self, z):
        """ReLU функция активации"""
        return np.maximum(0, z)

    def _relu_derivative(self, z):
        """Производная ReLU функции"""
        return (z > 0).astype(float)

    def _softmax(self, z):
        """Функция активации Softmax"""
        exp_z = np.exp(z - np.max(z, axis=0, keepdims=True))  # Стабилизация
        return exp_z / np.sum(exp_z, axis=0, keepdims=True)

    def _forward_propagation(self, X):
        """
        Прямое распространение

        Returns:
        --------
        cache : dict
            Кэш с активациями и линейными комбинациями
        """
        cache = {'A0': X.T}
        A = X.T

        # Прямое распространение через скрытые слои
        L = len(self.layer_sizes) - 1

        for l in range(1, L):
            W = self.parameters[f'W{l}']
            b = self.parameters[f'b{l}']

            Z = np.dot(W, A) + b
            A = self._relu(Z)

            cache[f'Z{l}'] = Z
            cache[f'A{l}'] = A

        # Выходной слой (Softmax)
        W = self.parameters[f'W{L}']
        b = self.parameters[f'b{L}']

        Z = np.dot(W, cache[f'A{L - 1}']) + b
        A = self._softmax(Z)

        cache[f'Z{L}'] = Z
        cache[f'A{L}'] = A

        return cache

    def _compute_loss(self, AL, Y):
        """
        Вычисление функции потерь (кросс-энтропия + L2 регуляризация)
        """
        m = Y.shape[1]

        # Кросс-энтропия
        loss = -np.sum(Y * np.log(AL + 1e-8)) / m

        # L2 регуляризация
        L = len(self.layer_sizes) - 1
        reg_loss = 0
        for l in range(1, L + 1):
            W = self.parameters[f'W{l}']
            reg_loss += np.sum(W * W)

        reg_loss = (self.reg_lambda / (2 * m)) * reg_loss

        return loss + reg_loss

    def _backward_propagation(self, X, Y, cache):
        """
        Обратное распространение ошибки

        Returns:
        --------
        grads : dict
            Градиенты параметров
        """
        m = X.shape[0]
        grads = {}
        L = len(self.layer_sizes) - 1

        # Градиент выходного слоя
        AL = cache[f'A{L}']
        dZ = AL - Y.T

        grads[f'dW{L}'] = np.dot(dZ, cache[f'A{L - 1}'].T) / m
        grads[f'db{L}'] = np.sum(dZ, axis=1, keepdims=True) / m

        # Добавление регуляризации
        grads[f'dW{L}'] += (self.reg_lambda / m) * self.parameters[f'W{L}']

        # Распространение через скрытые слои
        for l in reversed(range(1, L)):
            dA = np.dot(self.parameters[f'W{l + 1}'].T, dZ)
            dZ = dA * self._relu_derivative(cache[f'Z{l}'])

            grads[f'dW{l}'] = np.dot(dZ, cache[f'A{l - 1}'].T) / m
            grads[f'db{l}'] = np.sum(dZ, axis=1, keepdims=True) / m

            # Добавление регуляризации
            grads[f'dW{l}'] += (self.reg_lambda / m) * self.parameters[f'W{l}']

        return grads

    def _update_parameters(self, grads):
        """Обновление параметров с помощью градиентного спуска"""
        L = len(self.layer_sizes) - 1

        for l in range(1, L + 1):
            self.parameters[f'W{l}'] -= self.learning_rate * grads[f'dW{l}']
            self.parameters[f'b{l}'] -= self.learning_rate * grads[f'b{l}']

    def predict(self, X):
        """Предсказание класса для входных данных"""
        cache = self._forward_propagation(X)
        AL = cache[f'A{len(self.layer_sizes) - 1}']
        predictions = np.argmax(AL, axis=0)
        return predictions

    def predict_proba(self, X):
        """Вероятности классов для входных данных"""
        cache = self._forward_propagation(X)
        AL = cache[f'A{len(self.layer_sizes) - 1}']
        return AL.T

    def compute_accuracy(self, X, Y):
        """Вычисление точности предсказаний"""
        predictions = self.predict(X)
        true_labels = np.argmax(Y, axis=1)
        accuracy = np.mean(predictions == true_labels)
        return accuracy

    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=100, batch_size=64, verbose=True):
        """
        Обучение нейронной сети

        Parameters:
        -----------
        X_train, y_train : тренировочные данные
        X_val, y_val : валидационные данные (опционально)
        epochs : количество эпох
        batch_size : размер мини-батча
        verbose : вывод информации о процессе обучения
        """
        n_samples = X_train.shape[0]
        n_batches = int(np.ceil(n_samples / batch_size))

        print(f"Начало обучения:")
        print(f"  Эпох: {epochs}")
        print(f"  Размер батча: {batch_size}")
        print(f"  Количество батчей: {n_batches}")
        print("-" * 50)

        for epoch in range(epochs):
            start_time = time.time()

            # Перемешивание данных
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_loss = 0

            # Обучение по мини-батчам
            for batch in range(n_batches):
                start = batch * batch_size
                end = min(start + batch_size, n_samples)

                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # Прямое распространение
                cache = self._forward_propagation(X_batch)
                AL = cache[f'A{len(self.layer_sizes) - 1}']

                # Вычисление потерь
                batch_loss = self._compute_loss(AL, y_batch)
                epoch_loss += batch_loss

                # Обратное распространение
                grads = self._backward_propagation(X_batch, y_batch, cache)

                # Обновление параметров
                self._update_parameters(grads)

            # Средние потери за эпоху
            epoch_loss /= n_batches

            # Вычисление точности
            train_accuracy = self.compute_accuracy(X_train, y_train)

            # Сохранение истории
            self.history['loss'].append(epoch_loss)
            self.history['accuracy'].append(train_accuracy)

            # Валидация (если данные предоставлены)
            val_accuracy = None
            val_loss = None

            if X_val is not None and y_val is not None:
                cache_val = self._forward_propagation(X_val)
                AL_val = cache_val[f'A{len(self.layer_sizes) - 1}']
                val_loss = self._compute_loss(AL_val, y_val)
                val_accuracy = self.compute_accuracy(X_val, y_val)

                self.history['val_loss'].append(val_loss)
                self.history['val_accuracy'].append(val_accuracy)

            # Вывод информации
            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                epoch_time = time.time() - start_time
                output = f"Эпоха {epoch + 1:3d}/{epochs}"
                output += f" - Потери: {epoch_loss:.4f}"
                output += f" - Точность: {train_accuracy:.4f}"

                if val_accuracy is not None:
                    output += f" - Валидация: {val_accuracy:.4f}"

                output += f" - Время: {epoch_time:.2f}с"
                print(output)

        print("-" * 50)
        print("Обучение завершено!")

    def plot_training_history(self):
        """Построение графиков обучения"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # График функции потерь
        axes[0].plot(self.history['loss'], label='Обучающая', linewidth=2)
        if 'val_loss' in self.history and self.history['val_loss']:
            axes[0].plot(self.history['val_loss'], label='Валидационная', linewidth=2)
        axes[0].set_title('Функция потерь', fontsize=14)
        axes[0].set_xlabel('Эпоха', fontsize=12)
        axes[0].set_ylabel('Потери', fontsize=12)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # График точности
        axes[1].plot(self.history['accuracy'], label='Обучающая', linewidth=2)
        if 'val_accuracy' in self.history and self.history['val_accuracy']:
            axes[1].plot(self.history['val_accuracy'], label='Валидационная', linewidth=2)
        axes[1].set_title('Точность', fontsize=14)
        axes[1].set_xlabel('Эпоха', fontsize=12)
        axes[1].set_ylabel('Точность', fontsize=12)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def evaluate(self, X_test, y_test):
        """Оценка модели на тестовых данных"""
        print("\n" + "=" * 50)
        print("ОЦЕНКА МОДЕЛИ НА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 50)

        # Вычисление точности
        test_accuracy = self.compute_accuracy(X_test, y_test)
        print(f"Точность на тестовых данных: {test_accuracy:.4f}")

        # Подробный отчет по классам
        predictions = self.predict(X_test)
        true_labels = np.argmax(y_test, axis=1)

        print("\nОтчет по классам:")
        print("-" * 30)

        for digit in range(10):
            mask = true_labels == digit
            if np.sum(mask) > 0:
                class_accuracy = np.mean(predictions[mask] == true_labels[mask])
                print(f"Цифра {digit}: {class_accuracy:.4f} "
                      f"({np.sum(mask)} примеров)")

        # Матрица ошибок
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(true_labels, predictions)

        # Визуализация матрицы ошибок
        plt.figure(figsize=(10, 8))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title('Матрица ошибок', fontsize=16)
        plt.colorbar()

        tick_marks = np.arange(10)
        plt.xticks(tick_marks, range(10))
        plt.yticks(tick_marks, range(10))

        # Добавление чисел в ячейки
        thresh = cm.max() / 2.
        for i in range(10):
            for j in range(10):
                plt.text(j, i, format(cm[i, j], 'd'),
                         ha="center", va="center",
                         color="white" if cm[i, j] > thresh else "black")

        plt.ylabel('Истинная метка', fontsize=12)
        plt.xlabel('Предсказанная метка', fontsize=12)
        plt.tight_layout()
        plt.show()

        return test_accuracy


# Основная функция
def main():
    """Основная функция для обучения и оценки модели"""
    # Загрузка данных
    X_train, X_test, y_train, y_test, y_original = load_mnist_data()

    # Разделение тренировочных данных на обучение и валидацию
    X_train_final, X_val, y_train_final, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42
    )

    # Создание нейронной сети
    print("\nСоздание нейронной сети...")
    layer_sizes = [784, 128, 64, 10]  # Вход: 784 пикселя, 2 скрытых слоя, выход: 10 классов

    # Попробуйте разные гиперпараметры
    learning_rates = [0.01, 0.05, 0.1]
    batch_sizes = [32, 64, 128]

    best_accuracy = 0
    best_model = None
    best_params = {}

    print("\n" + "=" * 50)
    print("НАСТРОЙКА ГИПЕРПАРАМЕТРОВ")
    print("=" * 50)

    for lr in learning_rates:
        for batch_size in batch_sizes:
            print(f"\nТестирование параметров: learning_rate={lr}, batch_size={batch_size}")

            # Создание и обучение модели
            model = NeuralNetwork(
                layer_sizes=layer_sizes,
                learning_rate=lr,
                reg_lambda=0.001
            )

            # Быстрое обучение для настройки параметров
            model.train(
                X_train_final, y_train_final,
                X_val, y_val,
                epochs=30,
                batch_size=batch_size,
                verbose=False
            )

            # Оценка на валидационных данных
            val_accuracy = model.compute_accuracy(X_val, y_val)
            print(f"  Валидационная точность: {val_accuracy:.4f}")

            if val_accuracy > best_accuracy:
                best_accuracy = val_accuracy
                best_model = model
                best_params = {'learning_rate': lr, 'batch_size': batch_size}

    print(f"\nЛучшие параметры: {best_params}")
    print(f"Лучшая валидационная точность: {best_accuracy:.4f}")

    # Обучение лучшей модели на всех тренировочных данных
    print("\n" + "=" * 50)
    print("ОБУЧЕНИЕ ЛУЧШЕЙ МОДЕЛИ")
    print("=" * 50)

    final_model = NeuralNetwork(
        layer_sizes=layer_sizes,
        learning_rate=best_params['learning_rate'],
        reg_lambda=0.001
    )

    # Обучение на всех тренировочных данных
    final_model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=100,
        batch_size=best_params['batch_size'],
        verbose=True
    )

    # Построение графиков обучения
    print("\nПостроение графиков обучения...")
    final_model.plot_training_history()

    # Оценка на тестовых данных
    final_model.evaluate(X_test, y_test)

    # Демонстрация работы на нескольких примерах
    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ МОДЕЛИ")
    print("=" * 50)

    # Выбор нескольких случайных примеров
    indices = np.random.choice(len(X_test), 10, replace=False)
    demo_images = X_test[indices]
    demo_labels = np.argmax(y_test[indices], axis=1)

    predictions = final_model.predict(demo_images)
    probabilities = final_model.predict_proba(demo_images)

    # Визуализация предсказаний
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.ravel()

    for i in range(10):
        img = demo_images[i].reshape(28, 28)
        axes[i].imshow(img, cmap='gray')
        axes[i].axis('off')

        pred = predictions[i]
        true = demo_labels[i]
        prob = probabilities[i, pred]

        color = 'green' if pred == true else 'red'
        axes[i].set_title(f"Истина: {true}\nПредсказание: {pred}\nВероятность: {prob:.2f}",
                          color=color, fontsize=10)

    plt.suptitle('Демонстрация работы модели на тестовых данных', fontsize=14)
    plt.tight_layout()
    plt.show()

    # Сохранение параметров модели
    print("\nСохранение параметров модели...")
    np.savez('mnist_model_params.npz', **final_model.parameters)
    print("Параметры модели сохранены в файл 'mnist_model_params.npz'")


# Запуск основной функции
if __name__ == "__main__":
    main()