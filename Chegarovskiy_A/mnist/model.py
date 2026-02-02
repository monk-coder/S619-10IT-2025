import numpy as np
import pickle
import urllib.request
import gzip
import os
from typing import List, Tuple, Dict
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt


class NeuralNetwork:
    def __init__(self, layers: List[int], learning_rate: float = 0.01, 
                 reg_lambda: float = 0.001):
        self.layers = layers
        self.lr = learning_rate
        self.reg = reg_lambda
        self.L = len(layers) - 1
        
        self.weights = []
        self.biases = []
        
        for i in range(self.L):
            limit = np.sqrt(2.0 / layers[i])
            w = np.random.randn(layers[i+1], layers[i]) * limit
            b = np.zeros((layers[i+1], 1))
            self.weights.append(w)
            self.biases.append(b)
    
    def relu(self, Z: np.ndarray) -> np.ndarray:
        return np.maximum(0, Z)
    
    def softmax(self, Z: np.ndarray) -> np.ndarray:
        exp_Z = np.exp(Z - np.max(Z, axis=0, keepdims=True))
        return exp_Z / np.sum(exp_Z, axis=0, keepdims=True)
    
    def forward(self, X: np.ndarray) -> Tuple[Dict, Dict]:
        cache_A = {'A0': X.T}
        cache_Z = {}
        
        for l in range(self.L - 1):
            Z = self.weights[l] @ cache_A[f'A{l}'] + self.biases[l]
            cache_Z[f'Z{l+1}'] = Z
            cache_A[f'A{l+1}'] = self.relu(Z)
        
        Z = self.weights[-1] @ cache_A[f'A{self.L-1}'] + self.biases[-1]
        cache_Z[f'Z{self.L}'] = Z
        cache_A[f'A{self.L}'] = self.softmax(Z)
        
        return cache_A, cache_Z
    
    def compute_loss(self, Y_pred: np.ndarray, Y_true: np.ndarray) -> float:
        m = Y_true.shape[1]
        
        Y_pred = np.clip(Y_pred, 1e-15, 1 - 1e-15)
        ce = -np.sum(Y_true * np.log(Y_pred)) / m
        
        l2 = sum(np.sum(np.square(w)) for w in self.weights)
        l2 = (self.reg / (2 * m)) * l2
        
        return ce + l2
    
    def backward(self, X: np.ndarray, Y: np.ndarray, 
                 cache_A: Dict, cache_Z: Dict) -> Dict:
        m = X.shape[0]
        grads = {'dW': [], 'db': []}
        
        dZ = cache_A[f'A{self.L}'] - Y.T
        dW = (dZ @ cache_A[f'A{self.L-1}'].T) / m + (self.reg / m) * self.weights[-1]
        db = np.sum(dZ, axis=1, keepdims=True) / m
        grads['dW'].insert(0, dW)
        grads['db'].insert(0, db)
        
        for l in reversed(range(self.L - 1)):
            dA = self.weights[l+1].T @ dZ
            dZ = dA * (cache_Z[f'Z{l+1}'] > 0).astype(float)
            dW = (dZ @ cache_A[f'A{l}'].T) / m + (self.reg / m) * self.weights[l]
            db = np.sum(dZ, axis=1, keepdims=True) / m
            grads['dW'].insert(0, dW)
            grads['db'].insert(0, db)
        
        return grads
    
    def update(self, grads: Dict):
        for l in range(self.L):
            self.weights[l] -= self.lr * grads['dW'][l]
            self.biases[l] -= self.lr * grads['db'][l]
    
    def train_epoch(self, X: np.ndarray, Y: np.ndarray, 
                   batch_size: int = 32) -> Tuple[float, float]:
        m = X.shape[0]
        indices = np.random.permutation(m)
        X_shuffled = X[indices]
        Y_shuffled = Y[indices]
        
        epoch_loss = 0
        
        for i in range(0, m, batch_size):
            X_batch = X_shuffled[i:i+batch_size]
            Y_batch = Y_shuffled[i:i+batch_size]
            
            cache_A, cache_Z = self.forward(X_batch)
            loss = self.compute_loss(cache_A[f'A{self.L}'], Y_batch.T)
            epoch_loss += loss * X_batch.shape[0]
            
            grads = self.backward(X_batch, Y_batch, cache_A, cache_Z)
            self.update(grads)
        
        predictions = self.predict(X)
        accuracy = np.mean(predictions == np.argmax(Y, axis=1))
        
        return epoch_loss / m, accuracy
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        cache_A, _ = self.forward(X)
        return np.argmax(cache_A[f'A{self.L}'], axis=0)
    
    def evaluate(self, X: np.ndarray, Y: np.ndarray) -> Tuple[float, float]:
        cache_A, _ = self.forward(X)
        loss = self.compute_loss(cache_A[f'A{self.L}'], Y.T)
        predictions = np.argmax(cache_A[f'A{self.L}'], axis=0)
        accuracy = np.mean(predictions == np.argmax(Y, axis=1))
        return loss, accuracy
    
    def save(self, filename: str = 'model.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
        print(f"Модель сохранена: {filename}")
    
    @staticmethod
    def load(filename: str = 'model.pkl'):
        with open(filename, 'rb') as f:
            model = pickle.load(f)
        print(f"Модель загружена: {filename}")
        return model


def load_mnist() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    files = {
        'train_images': 'train-images-idx3-ubyte.gz',
        'train_labels': 'train-labels-idx1-ubyte.gz',
        'test_images': 't10k-images-idx3-ubyte.gz',
        'test_labels': 't10k-labels-idx1-ubyte.gz'
    }
    
    sources = [
        "https://storage.googleapis.com/cvdf-datasets/mnist/",
        "http://yann.lecun.com/exdb/mnist/",
    ]
    
    def download_file(filename: str) -> bool:
        for source in sources:
            try:
                url = source + filename
                print(f"Загрузка {filename}...")
                urllib.request.urlretrieve(url, filename)
                return True
            except:
                continue
        return False
    
    for filename in files.values():
        if not os.path.exists(filename):
            if not download_file(filename):
                raise Exception(f"Не удалось загрузить {filename}")
    
    def read_images(filename: str) -> np.ndarray:
        with gzip.open(filename, 'rb') as f:
            f.read(4)
            n = int.from_bytes(f.read(4), 'big')
            rows = int.from_bytes(f.read(4), 'big')
            cols = int.from_bytes(f.read(4), 'big')
            data = np.frombuffer(f.read(), dtype=np.uint8)
            return data.reshape(n, rows * cols) / 255.0
    
    def read_labels(filename: str) -> np.ndarray:
        with gzip.open(filename, 'rb') as f:
            f.read(4)
            n = int.from_bytes(f.read(4), 'big')
            return np.frombuffer(f.read(), dtype=np.uint8)
    
    print("Загрузка MNIST...")
    X_train = read_images(files['train_images'])
    y_train = read_labels(files['train_labels'])
    X_test = read_images(files['test_images'])
    y_test = read_labels(files['test_labels'])
    
    print(f"Обучающих: {X_train.shape[0]}")
    print(f"Тестовых:  {X_test.shape[0]}")
    
    return X_train, y_train, X_test, y_test


def one_hot_encode(y: np.ndarray, n_classes: int = 10) -> np.ndarray:
    return np.eye(n_classes)[y]


def plot_results(history: Dict, y_true: np.ndarray, y_pred: np.ndarray):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    axes[0].plot(history['train_loss'], 'b-', label='Train', linewidth=2)
    axes[0].plot(history['val_loss'], 'r-', label='Validation', linewidth=2)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(history['train_acc'], 'b-', label='Train', linewidth=2)
    axes[1].plot(history['val_acc'], 'r-', label='Validation', linewidth=2)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('loss_accuracy.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    plt.figure(figsize=(10, 8))
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("Графики сохранены: loss_accuracy.png, confusion_matrix.png")


def save_report(history: Dict, test_accuracy: float, params: Dict):
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("MNIST NEURAL NETWORK TRAINING REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("MODEL ARCHITECTURE\n")
        f.write(f"  Layers: {params['layers']}\n")
        
        f.write("TRAINING PARAMETERS\n")
        f.write(f"  Learning rate: {params['lr']}\n")
        f.write(f"  Batch size: {params['batch_size']}\n")
        f.write(f"  Epochs: {params['epochs']}\n")
        f.write(f"  L2 regularization: {params['reg']}\n")
        f.write(f"  Validation size: {params['val_size']}\n\n")
        
        f.write("RESULTS\n")
        f.write(f"  Final train accuracy: {history['train_acc'][-1]:.2%}\n")
        f.write(f"  Final validation accuracy: {history['val_acc'][-1]:.2%}\n")
        f.write(f"  Test accuracy: {test_accuracy:.2%}\n\n")
        
        f.write("TRAINING HISTORY (last 5 epochs)\n")
        start = max(0, len(history['train_acc']) - 5)
        for i in range(start, len(history['train_acc'])):
            f.write(f"  Epoch {i+1:3d}: "
                   f"Loss={history['train_loss'][i]:.4f}, "
                   f"Train Acc={history['train_acc'][i]:.4f}, "
                   f"Val Acc={history['val_acc'][i]:.4f}\n")
    
    print("Отчет сохранен: report.txt")
