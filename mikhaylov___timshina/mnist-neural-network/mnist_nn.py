import numpy as np
import struct
import gzip
import os
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional
import pickle

class MNISTLoader:
    """Класс для загрузки датасета MNIST"""
    
    @staticmethod
    def load_mnist(path: str, kind: str = 'train') -> Tuple[np.ndarray, np.ndarray]:
        """
        Загружает данные MNIST из файлов в формате IDX
        
        Параметры:
        ----------
        path : str
            Путь к папке с файлами MNIST
        kind : str
            Тип данных: 'train' или 't10k' (test)
            
        Возвращает:
        -----------
        images : np.ndarray
            Массив изображений формы (n_samples, 784)
        labels : np.ndarray
            Массив меток формы (n_samples,)
        """
        labels_path = os.path.join(path, f'{kind}-labels-idx1-ubyte.gz')
        images_path = os.path.join(path, f'{kind}-images-idx3-ubyte.gz')
        
        # Загрузка меток
        with gzip.open(labels_path, 'rb') as lbpath:
            magic, n = struct.unpack('>II', lbpath.read(8))
            labels = np.frombuffer(lbpath.read(), dtype=np.uint8)
        
        # Загрузка изображений
        with gzip.open(images_path, 'rb') as imgpath:
            magic, num, rows, cols = struct.unpack('>IIII', imgpath.read(16))
            images = np.frombuffer(imgpath.read(), dtype=np.uint8)
            images = images.reshape(num, rows * cols)
            
        return images, labels
    
    @staticmethod
    def download_mnist(data_dir: str = 'data') -> None:
        """Загружает датасет MNIST, если он отсутствует локально"""
        import urllib.request
        import os
        
        base_url = 'http://yann.lecun.com/exdb/mnist/'
        files = [
            'train-images-idx3-ubyte.gz',
            'train-labels-idx1-ubyte.gz',
            't10k-images-idx3-ubyte.gz', 
            't10k-labels-idx1-ubyte.gz'
        ]
        
        os.makedirs(data_dir, exist_ok=True)
        
        for file in files:
            filepath = os.path.join(data_dir, file)
            if not os.path.exists(filepath):
                print(f'Загрузка {file}...')
                urllib.request.urlretrieve(base_url + file, filepath)
                print(f'Загружено: {file}')


class NeuralNetwork:
    """Реализация полносвязной нейронной сети с нуля"""
    
    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.1, 
                 random_seed: int = 42):
        """
        Инициализация нейронной сети
        
        Параметры:
        ----------
        layer_sizes : List[int]
            Список размеров слоев (включая входной и выходной)
        learning_rate : float
            Скорость обучения
        random_seed : int
            Seed для воспроизводимости
        """
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.random_seed = random_seed
        self.params = {}
        self.grads = {}
        self.cache = {}
        self.loss_history = []
        self.accuracy_history = []
        
        self._initialize_parameters()
    
    def _initialize_parameters(self) -> None:
        """Инициализация весов и смещений"""
        np.random.seed(self.random_seed)
        
        for l in range(1, len(self.layer_sizes)):
            # Инициализация Хе (He initialization) для ReLU
            scale = np.sqrt(2.0 / self.layer_sizes[l-1])
            self.params[f'W{l}'] = np.random.randn(
                self.layer_sizes[l], self.layer_sizes[l-1]) * scale
            self.params[f'b{l}'] = np.zeros((self.layer_sizes[l], 1))
    
    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Сигмоидальная функция активации"""
        return 1.0 / (1.0 + np.exp(-np.clip(z, -100, 100)))
    
    def _relu(self, z: np.ndarray) -> np.ndarray:
        """Функция активации ReLU"""
        return np.maximum(0, z)
    
    def _softmax(self, z: np.ndarray) -> np.ndarray:
        """Функция активации Softmax"""
        exp_z = np.exp(z - np.max(z, axis=0, keepdims=True))
        return exp_z / np.sum(exp_z, axis=0, keepdims=True)
    
    def _sigmoid_derivative(self, a: np.ndarray) -> np.ndarray:
        """Производная сигмоидальной функции"""
        return a * (1 - a)
    
    def _relu_derivative(self, z: np.ndarray) -> np.ndarray:
        """Производная функции ReLU"""
        return (z > 0).astype(float)
    
    def forward_propagation(self, X: np.ndarray) -> np.ndarray:
        """
        Прямое распространение
        
        Параметры:
        ----------
        X : np.ndarray
            Входные данные формы (n_features, n_samples)
            
        Возвращает:
        -----------
        AL : np.ndarray
            Выход последнего слоя
        """
        A = X
        L = len(self.layer_sizes) - 1
        
        # Скрытые слои
        for l in range(1, L):
            W = self.params[f'W{l}']
            b = self.params[f'b{l}']
            
            Z = np.dot(W, A) + b
            A = self._relu(Z)
            
            # Сохранение значений для обратного распространения
            self.cache[f'Z{l}'] = Z
            self.cache[f'A{l}'] = A
        
        # Выходной слой
        W = self.params[f'W{L}']
        b = self.params[f'b{L}']
        Z = np.dot(W, A) + b
        AL = self._softmax(Z)
        
        self.cache[f'Z{L}'] = Z
        self.cache[f'A{L}'] = AL
        self.cache['A0'] = X
        
        return AL
    
    def compute_cost(self, AL: np.ndarray, Y: np.ndarray) -> float:
        """
        Вычисление функции потерь (кросс-энтропия)
        
        Параметры:
        ----------
        AL : np.ndarray
            Предсказания модели
        Y : np.ndarray
            Истинные метки в one-hot encoding
            
        Возвращает:
        -----------
        cost : float
            Значение функции потерь
        """
        m = Y.shape[1]
        
        # Кросс-энтропия с устойчивостью к log(0)
        eps = 1e-15
        AL_clipped = np.clip(AL, eps, 1 - eps)
        cost = -np.sum(Y * np.log(AL_clipped)) / m
        
        return cost
    
    def backward_propagation(self, AL: np.ndarray, Y: np.ndarray) -> None:
        """
        Обратное распространение ошибки
        
        Параметры:
        ----------
        AL : np.ndarray
            Предсказания модели
        Y : np.ndarray
            Истинные метки в one-hot encoding
        """
        m = Y.shape[1]
        L = len(self.layer_sizes) - 1
        
        # Градиент выходного слоя
        dZ = AL - Y
        self.grads[f'dW{L}'] = np.dot(dZ, self.cache[f'A{L-1}'].T) / m
        self.grads[f'db{L}'] = np.sum(dZ, axis=1, keepdims=True) / m
        
        # Градиенты скрытых слоев
        for l in reversed(range(1, L)):
            dA = np.dot(self.params[f'W{l+1}'].T, dZ)
            dZ = dA * self._relu_derivative(self.cache[f'Z{l}'])
            
            A_prev = self.cache[f'A{l-1}'] if l > 1 else self.cache['A0']
            self.grads[f'dW{l}'] = np.dot(dZ, A_prev.T) / m
            self.grads[f'db{l}'] = np.sum(dZ, axis=1, keepdims=True) / m
    
    def update_parameters(self) -> None:
        """Обновление параметров с использованием градиентного спуска"""
        L = len(self.layer_sizes) - 1
        
        for l in range(1, L + 1):
            self.params[f'W{l}'] -= self.learning_rate * self.grads[f'dW{l}']
            self.params[f'b{l}'] -= self.learning_rate * self.grads[f'db{l}']
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Предсказание классов для входных данных
        
        Параметры:
        ----------
        X : np.ndarray
            Входные данные
            
        Возвращает:
        -----------
        predictions : np.ndarray
            Предсказанные классы
        """
        AL = self.forward_propagation(X)
        predictions = np.argmax(AL, axis=0)
        return predictions
    
    def compute_accuracy(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Вычисление точности модели
        
        Параметры:
        ----------
        X : np.ndarray
            Входные данные
        Y : np.ndarray
            Истинные метки (не one-hot)
            
        Возвращает:
        -----------
        accuracy : float
            Точность модели
        """
        predictions = self.predict(X)
        accuracy = np.mean(predictions == Y)
        return accuracy
    
    def train(self, X_train: np.ndarray, Y_train: np.ndarray, 
              X_val: Optional[np.ndarray] = None, Y_val: Optional[np.ndarray] = None,
              epochs: int = 100, batch_size: int = 32, verbose: bool = True) -> None:
        """
        Обучение модели
        
        Параметры:
        ----------
        X_train : np.ndarray
            Обучающие данные
        Y_train : np.ndarray
            Обучающие метки в one-hot encoding
        X_val : np.ndarray, optional
            Валидационные данные
        Y_val : np.ndarray, optional
            Валидационные метки
        epochs : int
            Количество эпох
        batch_size : int
            Размер батча
        verbose : bool
            Вывод информации о процессе обучения
        """
        m = X_train.shape[1]
        
        for epoch in range(epochs):
            # Перемешивание данных
            permutation = np.random.permutation(m)
            X_shuffled = X_train[:, permutation]
            Y_shuffled = Y_train[:, permutation]
            
            epoch_loss = 0
            num_batches = 0
            
            # Мини-батчи
            for i in range(0, m, batch_size):
                # Получение мини-батча
                end = min(i + batch_size, m)
                X_batch = X_shuffled[:, i:end]
                Y_batch = Y_shuffled[:, i:end]
                
                # Прямое распространение
                AL = self.forward_propagation(X_batch)
                
                # Вычисление потерь
                batch_loss = self.compute_cost(AL, Y_batch)
                epoch_loss += batch_loss
                
                # Обратное распространение
                self.backward_propagation(AL, Y_batch)
                
                # Обновление параметров
                self.update_parameters()
                
                num_batches += 1
            
            # Средняя потеря за эпоху
            avg_loss = epoch_loss / num_batches
            self.loss_history.append(avg_loss)
            
            # Вычисление точности
            train_accuracy = self.compute_accuracy(X_train, 
                                                  np.argmax(Y_train, axis=0))
            self.accuracy_history.append(train_accuracy)
            
            # Валидационная точность
            val_accuracy = None
            if X_val is not None and Y_val is not None:
                val_accuracy = self.compute_accuracy(X_val, Y_val)
            
            # Вывод информации
            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                msg = f"Эпоха {epoch+1}/{epochs} - Loss: {avg_loss:.4f} - "
                msg += f"Train Accuracy: {train_accuracy:.4f}"
                if val_accuracy is not None:
                    msg += f" - Val Accuracy: {val_accuracy:.4f}"
                print(msg)
    
    def plot_training_history(self, save_path: Optional[str] = None) -> None:
        """
        Построение графиков обучения
        
        Параметры:
        ----------
        save_path : str, optional
            Путь для сохранения графиков
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # График функции потерь
        ax1.plot(self.loss_history)
        ax1.set_title('Функция потерь во время обучения')
        ax1.set_xlabel('Эпоха')
        ax1.set_ylabel('Loss')
        ax1.grid(True)
        
        # График точности
        ax2.plot(self.accuracy_history)
        ax2.set_title('Точность во время обучения')
        ax2.set_xlabel('Эпоха')
        ax2.set_ylabel('Accuracy')
        ax2.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_model(self, filepath: str) -> None:
        """Сохранение модели"""
        model_data = {
            'params': self.params,
            'layer_sizes': self.layer_sizes,
            'learning_rate': self.learning_rate,
            'loss_history': self.loss_history,
            'accuracy_history': self.accuracy_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    @classmethod
    def load_model(cls, filepath: str) -> 'NeuralNetwork':
        """Загрузка модели"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        model = cls(model_data['layer_sizes'], 
                   model_data['learning_rate'])
        model.params = model_data['params']
        model.loss_history = model_data['loss_history']
        model.accuracy_history = model_data['accuracy_history']
        
        return model


def preprocess_data(X: np.ndarray, Y: np.ndarray, num_classes: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Предобработка данных
    
    Параметры:
    ----------
    X : np.ndarray
        Входные данные
    Y : np.ndarray
        Метки классов
        
    Возвращает:
    -----------
    X_processed : np.ndarray
        Предобработанные данные
    Y_one_hot : np.ndarray
        Метки в one-hot encoding
    """
    # Нормализация пикселей к диапазону [0, 1]
    X_processed = X.astype(np.float32) / 255.0
    
    # Транспонирование для формата (features, samples)
    X_processed = X_processed.T
    
    # Преобразование меток в one-hot encoding
    Y_one_hot = np.zeros((num_classes, Y.shape[0]))
    Y_one_hot[Y, np.arange(Y.shape[0])] = 1
    
    return X_processed, Y_one_hot