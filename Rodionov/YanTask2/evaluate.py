import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import argparse

from neural_network import NeuralNetwork
from train import load_mnist_data

def plot_confusion_matrix(y_true, y_pred, save_path='confusion_matrix.png'):
    """
    Построение матрицы ошибок
    """
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

    return cm

def plot_sample_predictions(model, X, y_true, y_pred, save_path='sample_predictions.png'):
    """
    Визуализация примеров предсказаний
    """
    num_samples = 10
    sample_indices = np.random.choice(X.shape[1], num_samples, replace=False)

    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.ravel()

    for i, idx in enumerate(sample_indices):
        # Получение изображения
        image = X[:, idx].reshape(28, 28)

        # Получение предсказанных вероятностей
        activations, _ = model.forward_propagation(X[:, idx:idx+1])
        probs = activations[f'A{model.num_layers-1}'][:, 0]

        # Отображение
        axes[i].imshow(image, cmap='gray')
        axes[i].axis('off')

        true_label = y_true[idx]
        pred_label = y_pred[idx]

        color = 'green' if true_label == pred_label else 'red'
        axes[i].set_title(f'True: {true_label}\nPred: {pred_label}\nProb: {probs[pred_label]:.2f}',
                         color=color, fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Оценка обученной модели на MNIST')
    parser.add_argument('--model_path', type=str, default='mnist_model.pkl',
                       help='Путь к сохраненной модели')

    args = parser.parse_args()

    # Загрузка данных
    _, _, X_val, y_val, X_test, y_test, y_val_labels = load_mnist_data()

    # Загрузка модели
    print(f"Загрузка модели из {args.model_path}")
    model = NeuralNetwork.load_model(args.model_path)

    # Предсказания на валидационном наборе
    print("\nОценка на валидационном наборе:")
    val_predictions = model.predict(X_val)
    val_accuracy = model.accuracy(X_val, y_val)
    print(f"Точность на валидационном наборе: {val_accuracy:.4f}")

    # Матрица ошибок
    cm = plot_confusion_matrix(y_val_labels, val_predictions)

    # Отчет классификации
    print("\nОтчет классификации:")
    print(classification_report(y_val_labels, val_predictions,
                                target_names=[str(i) for i in range(10)]))

    # Визуализация примеров
    plot_sample_predictions(model, X_val, y_val_labels, val_predictions)

    # Оценка на тестовом наборе
    print("\nОценка на тестовом наборе:")
    test_predictions = model.predict(X_test)
    test_accuracy = model.accuracy(X_test, y_test)
    print(f"Точность на тестовом наборе: {test_accuracy:.4f}")

    # Анализ ошибок
    print("\nАнализ наиболее частых ошибок:")
    error_mask = (val_predictions != y_val_labels)
    error_indices = np.where(error_mask)[0]

    if len(error_indices) > 0:
        error_pairs = []
        for idx in error_indices[:10]:  # Первые 10 ошибок
            true_label = y_val_labels[idx]
            pred_label = val_predictions[idx]
            error_pairs.append((true_label, pred_label))

        from collections import Counter
        error_counts = Counter(error_pairs)
        print("Наиболее частые ошибки (истинный -> предсказанный):")
        for (true, pred), count in error_counts.most_common(5):
            print(f"  {true} -> {pred}: {count} раз")

if __name__ == "__main__":
    main()