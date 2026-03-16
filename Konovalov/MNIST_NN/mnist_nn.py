import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import time

class NeuralNetwork:
    """Нейронная сеть для классификации MNIST"""
    
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        self.W1 = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((hidden_size, 1))
        
        self.W2 = np.random.randn(output_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((output_size, 1))
        
        self.train_loss_history = []
        self.train_accuracy_history = []
        self.val_loss_history = []
        self.val_accuracy_history = []
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def sigmoid_derivative(self, x):
        return x * (1 - x)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=0, keepdims=True))
        return exp_x / np.sum(exp_x, axis=0, keepdims=True)
    
    def forward_propagation(self, X):
        """Прямое распространение (без z1, z2)"""
        a1 = self.sigmoid(np.dot(self.W1, X) + self.b1)
        a2 = self.softmax(np.dot(self.W2, a1) + self.b2)
        return a1, a2
    
    def compute_loss(self, y_true, y_pred):
        m = y_true.shape[1]
        loss = -np.sum(y_true * np.log(y_pred + 1e-8)) / m
        return loss
    
    def compute_accuracy(self, y_true, y_pred):
        if y_true.ndim == 2:
            y_true_indices = np.argmax(y_true, axis=0)
        else:
            y_true_indices = y_true
            
        if y_pred.ndim == 2:
            y_pred_indices = np.argmax(y_pred, axis=0)
        else:
            y_pred_indices = y_pred
            
        return np.mean(y_true_indices == y_pred_indices)
    
    def backward_propagation(self, X, y, a1, a2):
        """Обратное распространение (без z1, z2)"""
        m = X.shape[1]
        
        dz2 = a2 - y
        dW2 = np.dot(dz2, a1.T) / m
        db2 = np.sum(dz2, axis=1, keepdims=True) / m
        
        da1 = np.dot(self.W2.T, dz2)
        dz1 = da1 * self.sigmoid_derivative(a1)
        dW1 = np.dot(dz1, X.T) / m
        db1 = np.sum(dz1, axis=1, keepdims=True) / m
        
        return dW1, db1, dW2, db2
    
    def update_parameters(self, dW1, db1, dW2, db2):
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32, verbose=True):
        n_samples = X_train.shape[1]
        
        print(f"Начало обучения...")
        print(f"Эпохи: {epochs}, Размер батча: {batch_size}")
        print("-" * 50)
        
        start_time = time.time()
        
        for epoch in range(epochs):
            permutation = np.random.permutation(n_samples)
            X_shuffled = X_train[:, permutation]
            y_shuffled = y_train[:, permutation]
            
            epoch_loss = 0
            epoch_accuracy = 0
            
            for i in range(0, n_samples, batch_size):
                end_idx = min(i + batch_size, n_samples)
                X_batch = X_shuffled[:, i:end_idx]
                y_batch = y_shuffled[:, i:end_idx]
                
                a1, a2 = self.forward_propagation(X_batch)
                
                batch_loss = self.compute_loss(y_batch, a2)
                batch_accuracy = self.compute_accuracy(y_batch, a2)
                
                epoch_loss += batch_loss * (end_idx - i)
                epoch_accuracy += batch_accuracy * (end_idx - i)
                
                dW1, db1, dW2, db2 = self.backward_propagation(X_batch, y_batch, a1, a2)
                self.update_parameters(dW1, db1, dW2, db2)
            
            epoch_loss /= n_samples
            epoch_accuracy /= n_samples
            
            _, val_a2 = self.forward_propagation(X_val)
            val_loss = self.compute_loss(y_val, val_a2)
            val_accuracy = self.compute_accuracy(y_val, val_a2)
            
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
        _, a2 = self.forward_propagation(X)
        return np.argmax(a2, axis=0)


# ==================== ОТДЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ГРАФИКОВ ====================
def plot_training_results(models_info, save_path=None):
    """
    Отдельная функция для построения графиков обучения
    models_info: список словарей с информацией о моделях
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    colors = ['blue', 'green', 'red']
    
    for idx, model_info in enumerate(models_info):
        color = colors[idx % len(colors)]
        label = model_info['label']
        
        # График 1: Loss (train)
        axes[0, 0].plot(model_info['train_loss'], 
                       color=color, linestyle='-', label=f'{label} (train)')
        
        # График 1: Loss (val)
        axes[0, 0].plot(model_info['val_loss'], 
                       color=color, linestyle='--', label=f'{label} (val)')
    
    axes[0, 0].set_xlabel('Эпохи')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Функция потерь во время обучения')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    for idx, model_info in enumerate(models_info):
        color = colors[idx % len(colors)]
        label = model_info['label']
        
        # График 2: Accuracy (train)
        axes[0, 1].plot(model_info['train_accuracy'], 
                       color=color, linestyle='-', label=f'{label} (train)')
        
        # График 2: Accuracy (val)
        axes[0, 1].plot(model_info['val_accuracy'], 
                       color=color, linestyle='--', label=f'{label} (val)')
    
    axes[0, 1].set_xlabel('Эпохи')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Точность во время обучения')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # График 3: Сравнение финальных точностей
    labels = [m['label'] for m in models_info]
    train_accs = [m['train_accuracy'][-1] for m in models_info]
    val_accs = [m['val_accuracy'][-1] for m in models_info]
    
    x = np.arange(len(labels))
    width = 0.35
    
    axes[1, 0].bar(x - width/2, train_accs, width, label='Train Accuracy', color='lightblue')
    axes[1, 0].bar(x + width/2, val_accs, width, label='Val Accuracy', color='lightgreen')
    axes[1, 0].set_xlabel('Эксперименты')
    axes[1, 0].set_ylabel('Accuracy')
    axes[1, 0].set_title('Сравнение финальной точности')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(labels)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # График 4: Разница между train и val accuracy (переобучение)
    overfitting_gap = [train - val for train, val in zip(train_accs, val_accs)]
    axes[1, 1].bar(labels, overfitting_gap, color='orange')
    axes[1, 1].set_xlabel('Эксперименты')
    axes[1, 1].set_ylabel('Разница (Train - Val)')
    axes[1, 1].set_title('Степень переобучения\n(чем больше, тем сильнее переобучение)')
    axes[1, 1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def load_and_prepare_mnist(n_samples=10000):
    print("Загрузка данных MNIST...")
    
    mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='liac-arff')
    X = mnist.data
    y = mnist.target.astype(int)
    
    if n_samples < len(X):
        indices = np.random.choice(len(X), n_samples, replace=False)
        X = X[indices]
        y = y[indices]
    
    X = X.astype(np.float32) / 255.0
    
    # One-Hot Encoding: преобразуем цифры 0-9 в векторы
    encoder = OneHotEncoder(sparse_output=False, categories=[range(10)])
    y_onehot = encoder.fit_transform(y.reshape(-1, 1)).T
    
    X = X.T
    
    X_train, X_temp, y_train, y_temp = train_test_split(
        X.T, y_onehot.T, test_size=0.3, random_state=42, stratify=y
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y[:len(X_temp)]
    )
    
    return (
        X_train.T, y_train.T,
        X_val.T, y_val.T,
        X_test.T, y_test.T,
        y[:len(X_train)], y[len(X_train):len(X_train)+len(X_val)], y[len(X_train)+len(X_val):]
    )


def evaluate_model(model, X_test, y_test, y_test_labels):
    print("\n" + "="*50)
    print("ОЦЕНКА НА ТЕСТОВОЙ ВЫБОРКЕ")
    print("="*50)
    
    predictions = model.predict(X_test)
    test_accuracy = model.compute_accuracy(y_test_labels, predictions)
    print(f"Точность на тестовой выборке: {test_accuracy:.4f}")
    
    from sklearn.metrics import confusion_matrix, classification_report
    cm = confusion_matrix(y_test_labels, predictions)
    
    print("\nМатрица ошибок:")
    print(cm)
    
    print("\nОтчет по классификации:")
    print("Precision (Точность): % правильно предсказанных 'эта цифра' из всех предсказанных 'эта цифра'")
    print("Recall (Полнота): % правильно предсказанных 'эта цифра' из всех реальных 'эта цифра'")
    print("F1-score: баланс между Precision и Recall")
    print("Support: количество примеров каждого класса")
    print("-" * 60)
    print(classification_report(y_test_labels, predictions, digits=4))


def main():
    """Основная функция с экспериментами (меняется только 1 параметр)"""
    
    X_train, y_train_onehot, X_val, y_val_onehot, X_test, y_test_onehot, \
    y_train_labels, y_val_labels, y_test_labels = load_and_prepare_mnist(n_samples=20000)
    
    input_size = 784
    hidden_size = 128
    output_size = 10
    
    # Эксперимент 1: меняем ТОЛЬКО learning_rate
    experiments = [
        {'learning_rate': 0.1, 'epochs': 50, 'batch_size': 32, 'label': 'LR=0.1'},
        {'learning_rate': 0.05, 'epochs': 50, 'batch_size': 32, 'label': 'LR=0.05'},
        {'learning_rate': 0.01, 'epochs': 50, 'batch_size': 32, 'label': 'LR=0.01'},
    ]
    
    best_accuracy = 0
    best_model = None
    models_info = []  # Для хранения данных для графиков
    
    for exp in experiments:
        print(f"\n{'='*60}")
        print(f"Эксперимент: {exp['label']}")
        print('='*60)
        
        model = NeuralNetwork(
            input_size=input_size,
            hidden_size=hidden_size,
            output_size=output_size,
            learning_rate=exp['learning_rate']
        )
        
        model.train(
            X_train=X_train,
            y_train=y_train_onehot,
            X_val=X_val,
            y_val=y_val_onehot,
            epochs=exp['epochs'],
            batch_size=exp['batch_size'],
            verbose=True
        )
        
        val_accuracy = model.val_accuracy_history[-1]
        
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_model = model
        
        # Сохраняем данные для графиков
        models_info.append({
            'label': exp['label'],
            'train_loss': model.train_loss_history,
            'val_loss': model.val_loss_history,
            'train_accuracy': model.train_accuracy_history,
            'val_accuracy': model.val_accuracy_history,
            'learning_rate': exp['learning_rate']
        })
    
    # Строим графики ОТДЕЛЬНОЙ функцией
    plot_training_results(models_info, save_path='plots/all_experiments.png')
    
    print(f"\n{'='*60}")
    print(f"ЛУЧШАЯ МОДЕЛЬ: LR={best_model.learning_rate}")
    print(f"Точность на валидации: {best_accuracy:.4f}")
    print('='*60)
    
    evaluate_model(best_model, X_test, y_test_onehot, y_test_labels)
    
    return best_model, models_info


if __name__ == "__main__":
    import os
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    best_model, models_info = main()