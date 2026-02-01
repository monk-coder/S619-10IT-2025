import numpy as np
import os
from mnist_nn import MNISTLoader, NeuralNetwork, preprocess_data
import matplotlib.pyplot as plt

def main():
    # Параметры
    DATA_DIR = 'data'
    RESULTS_DIR = 'results'
    
    # Создание директорий
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("Загрузка датасета MNIST...")
    
    # Загрузка или скачивание датасета
    if not os.path.exists(DATA_DIR):
        MNISTLoader.download_mnist(DATA_DIR)
    
    # Загрузка данных
    X_train_raw, y_train_raw = MNISTLoader.load_mnist(DATA_DIR, 'train')
    X_test_raw, y_test_raw = MNISTLoader.load_mnist(DATA_DIR, 't10k')
    
    print(f"Обучающая выборка: {X_train_raw.shape[0]} изображений")
    print(f"Тестовая выборка: {X_test_raw.shape[0]} изображений")
    
    # Разделение обучающей выборки на train/val
    train_ratio = 0.8
    train_size = int(X_train_raw.shape[0] * train_ratio)
    
    X_train, y_train = X_train_raw[:train_size], y_train_raw[:train_size]
    X_val, y_val = X_train_raw[train_size:], y_train_raw[train_size:]
    
    # Предобработка данных
    print("Предобработка данных...")
    X_train_proc, y_train_one_hot = preprocess_data(X_train, y_train)
    X_val_proc, y_val_one_hot = preprocess_data(X_val, y_val)
    X_test_proc, y_test_one_hot = preprocess_data(X_test_raw, y_test_raw)
    
    # Параметры нейронной сети
    layer_sizes = [784, 128, 64, 10]  # 784 входа, 2 скрытых слоя, 10 выходов
    learning_rate = 0.1
    epochs = 50
    batch_size = 64
    
    print(f"\nАрхитектура сети: {layer_sizes}")
    print(f"Скорость обучения: {learning_rate}")
    print(f"Количество эпох: {epochs}")
    print(f"Размер батча: {batch_size}")
    
    # Создание и обучение модели
    print("\nНачало обучения...")
    model = NeuralNetwork(layer_sizes, learning_rate, random_seed=42)
    
    model.train(X_train_proc, y_train_one_hot, 
                X_val_proc, y_val_raw=y_val,
                epochs=epochs, batch_size=batch_size, verbose=True)
    
    # Оценка на тестовой выборке
    print("\nОценка на тестовой выборке...")
    test_accuracy = model.compute_accuracy(X_test_proc, y_test_raw)
    print(f"Точность на тестовой выборке: {test_accuracy:.4f}")
    
    # Построение графиков
    print("\nПостроение графиков обучения...")
    model.plot_training_history(save_path=os.path.join(RESULTS_DIR, 'training_history.png'))
    
    # Сохранение модели
    model.save_model(os.path.join(RESULTS_DIR, 'mnist_model.pkl'))
    print(f"Модель сохранена в {RESULTS_DIR}/mnist_model.pkl")
    
    # Визуализация примеров предсказаний
    visualize_predictions(model, X_test_proc, y_test_raw, X_test_raw, RESULTS_DIR)

def visualize_predictions(model, X_test, y_test, X_test_raw, results_dir, num_examples=10):
    """Визуализация примеров предсказаний"""
    # Выбор случайных примеров
    indices = np.random.choice(X_test.shape[1], num_examples, replace=False)
    sample_images = X_test[:, indices]
    true_labels = y_test[indices]
    
    # Получение предсказаний
    predictions = model.predict(sample_images)
    
    # Визуализация
    fig, axes = plt.subplots(2, 5, figsize=(12, 6))
    axes = axes.ravel()
    
    for i, idx in enumerate(indices):
        # Восстановление изображения
        img = X_test_raw[idx].reshape(28, 28)
        
        axes[i].imshow(img, cmap='gray')
        axes[i].set_title(f'True: {true_labels[i]}\nPred: {predictions[i]}', 
                         color='green' if true_labels[i] == predictions[i] else 'red')
        axes[i].axis('off')
    
    plt.suptitle('Примеры предсказаний модели', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'predictions_examples.png'), 
                dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    main()