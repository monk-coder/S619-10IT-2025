import numpy as np
import pickle
import urllib.request
import gzip
import os
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt


class NeuralNetwork:
    def __init__(self, layer_sizes, learning_rate=0.01, reg_lambda=0.001):
        self.layer_sizes = layer_sizes
        self.lr = learning_rate
        self.reg = reg_lambda
        self.layer_count = len(layer_sizes) - 1
        
        self.weights = []
        self.biases = []
        
        for i in range(self.layer_count):
            limit = np.sqrt(2.0 / layer_sizes[i])
            weight_matrix = np.random.randn(layer_sizes[i+1], layer_sizes[i]) * limit
            bias_vector = np.zeros((layer_sizes[i+1], 1))
            self.weights.append(weight_matrix)
            self.biases.append(bias_vector)
    
    def relu(self, matrix):
        return np.maximum(0, matrix)
    
    def softmax(self, matrix):
        exp_matrix = np.exp(matrix - np.max(matrix, axis=0, keepdims=True))
        return exp_matrix / np.sum(exp_matrix, axis=0, keepdims=True)
    
    def forward(self, inputs):
        activations = [inputs.T]
        linear_outputs = []
        
        for i in range(self.layer_count - 1):
            linear = self.weights[i] @ activations[-1] + self.biases[i]
            activation = self.relu(linear)
            linear_outputs.append(linear)
            activations.append(activation)
        
        linear = self.weights[-1] @ activations[-1] + self.biases[-1]
        activation = self.softmax(linear)
        linear_outputs.append(linear)
        activations.append(activation)
        
        return activations, linear_outputs
    
    def compute_loss(self, predictions, targets):
        m = targets.shape[1]
        
        predictions = np.clip(predictions, 1e-15, 1 - 1e-15)
        cross_entropy = -np.sum(targets * np.log(predictions)) / m
        
        l2_penalty = 0
        for w in self.weights:
            l2_penalty += np.sum(np.square(w))
        l2_penalty = (self.reg / (2 * m)) * l2_penalty
        
        return cross_entropy + l2_penalty
    
    def backward(self, inputs, targets, activations, linear_outputs):
        m = inputs.shape[0]
        gradients = {'dW': [], 'db': []}
        
        output_error = activations[-1] - targets.T
        
        weight_grad = (output_error @ activations[-2].T) / m
        weight_grad += (self.reg / m) * self.weights[-1]
        bias_grad = np.sum(output_error, axis=1, keepdims=True) / m
        
        gradients['dW'].insert(0, weight_grad)
        gradients['db'].insert(0, bias_grad)
        
        current_error = output_error
        
        for i in range(self.layer_count - 2, -1, -1):
            activation_grad = self.weights[i+1].T @ current_error
            linear_grad = activation_grad * (linear_outputs[i] > 0).astype(float)
            
            weight_grad = (linear_grad @ activations[i].T) / m
            weight_grad += (self.reg / m) * self.weights[i]
            bias_grad = np.sum(linear_grad, axis=1, keepdims=True) / m
            
            gradients['dW'].insert(0, weight_grad)
            gradients['db'].insert(0, bias_grad)
            
            current_error = linear_grad
        
        return gradients
    
    def update_weights(self, gradients):
        for i in range(self.layer_count):
            self.weights[i] -= self.lr * gradients['dW'][i]
            self.biases[i] -= self.lr * gradients['db'][i]
    
    def train_epoch(self, inputs, targets, batch_size=32):
        m = inputs.shape[0]
        indices = np.random.permutation(m)
        shuffled_inputs = inputs[indices]
        shuffled_targets = targets[indices]
        
        total_loss = 0
        
        for i in range(0, m, batch_size):
            batch_inputs = shuffled_inputs[i:i+batch_size]
            batch_targets = shuffled_targets[i:i+batch_size]
            
            activations, linear_outputs = self.forward(batch_inputs)
            loss_value = self.compute_loss(activations[-1], batch_targets.T)
            total_loss += loss_value * batch_inputs.shape[0]
            
            gradients = self.backward(batch_inputs, batch_targets, activations, linear_outputs)
            self.update_weights(gradients)
        
        predictions = self.predict(inputs)
        accuracy_value = np.mean(predictions == np.argmax(targets, axis=1))
        
        avg_loss = total_loss / m
        return avg_loss, accuracy_value
    
    def predict(self, inputs):
        activations, _ = self.forward(inputs)
        return np.argmax(activations[-1], axis=0)
    
    def evaluate(self, inputs, targets):
        activations, _ = self.forward(inputs)
        loss_value = self.compute_loss(activations[-1], targets.T)
        predictions = np.argmax(activations[-1], axis=0)
        accuracy_value = np.mean(predictions == np.argmax(targets, axis=1))
        return loss_value, accuracy_value
    
    def save_model(self, filename='model.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
        print(f"Модель сохранена: {filename}")
    
    @staticmethod
    def load_model(filename='model.pkl'):
        with open(filename, 'rb') as f:
            model = pickle.load(f)
        print(f"Модель загружена: {filename}")
        return model


def download_mnist_file(filename, sources):
    for source in sources:
        try:
            url = source + filename
            print(f"Загрузка {filename}...")
            urllib.request.urlretrieve(url, filename)
            return True
        except:
            continue
    return False


def read_image_file(filename):
    with gzip.open(filename, 'rb') as f:
        f.read(4)
        n_images = int.from_bytes(f.read(4), 'big')
        rows = int.from_bytes(f.read(4), 'big')
        cols = int.from_bytes(f.read(4), 'big')
        data = np.frombuffer(f.read(), dtype=np.uint8)
        return data.reshape(n_images, rows * cols) / 255.0


def read_label_file(filename):
    with gzip.open(filename, 'rb') as f:
        f.read(4)
        n_labels = int.from_bytes(f.read(4), 'big')
        return np.frombuffer(f.read(), dtype=np.uint8)


def load_mnist_data():
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
    
    for filename in files.values():
        if not os.path.exists(filename):
            if not download_mnist_file(filename, sources):
                raise Exception(f"Не удалось загрузить {filename}")
    
    print("Загрузка MNIST...")
    train_images = read_image_file(files['train_images'])
    train_labels = read_label_file(files['train_labels'])
    test_images = read_image_file(files['test_images'])
    test_labels = read_label_file(files['test_labels'])
    
    print(f"Обучающих: {train_images.shape[0]}")
    print(f"Тестовых:  {test_images.shape[0]}")
    
    return train_images, train_labels, test_images, test_labels


def create_training_plots(history, true_labels, predicted_labels):
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
    confusion = confusion_matrix(true_labels, predicted_labels)
    sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("Графики сохранены: loss_accuracy.png, confusion_matrix.png")


def save_training_report(history, test_accuracy, parameters):
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("MNIST NEURAL NETWORK TRAINING REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("MODEL ARCHITECTURE\n")
        f.write(f"  Layers: {parameters['layers']}\n")
        
        f.write("TRAINING PARAMETERS\n")
        f.write(f"  Learning rate: {parameters['lr']}\n")
        f.write(f"  Batch size: {parameters['batch_size']}\n")
        f.write(f"  Epochs: {parameters['epochs']}\n")
        f.write(f"  L2 regularization: {parameters['reg']}\n")
        f.write(f"  Validation size: {parameters['val_size']}\n\n")
        
        f.write("RESULTS\n")
        f.write(f"  Final train accuracy: {history['train_acc'][-1]:.2%}\n")
        f.write(f"  Final validation accuracy: {history['val_acc'][-1]:.2%}\n")
        f.write(f"  Test accuracy: {test_accuracy:.2%}\n\n")
        
        f.write("TRAINING HISTORY (last 5 epochs)\n")
        start_idx = max(0, len(history['train_acc']) - 5)
        for i in range(start_idx, len(history['train_acc'])):
            f.write(f"  Epoch {i+1:3d}: "
                   f"Loss={history['train_loss'][i]:.4f}, "
                   f"Train Acc={history['train_acc'][i]:.4f}, "
                   f"Val Acc={history['val_acc'][i]:.4f}\n")
    
    print("Отчет сохранен: report.txt")
