"""
utils.py
Вспомогательные функции для работы с MNIST
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import confusion_matrix


def load_mnist_data(test_size=0.2, random_state=42):
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
        X, y_one_hot, test_size=test_size, random_state=random_state
    )

    print(f"Данные загружены:")
    print(f"  Обучающая выборка: {X_train.shape[0]} изображений")
    print(f"  Тестовая выборка: {X_test.shape[0]} изображений")
    print(f"  Размер изображения: {X_train.shape[1]} пикселей")

    return X_train, X_test, y_train, y_test, y


def plot_training_history(history):
    """Построение графиков обучения"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # График функции потерь
    axes[0].plot(history['loss'], label='Обучающая', linewidth=2)
    if 'val_loss' in history and history['val_loss']:
        axes[0].plot(history['val_loss'], label='Валидационная', linewidth=2)
    axes[0].set_title('Функция потерь', fontsize=14)
    axes[0].set_xlabel('Эпоха', fontsize=12)
    axes[0].set_ylabel('Потери', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # График точности
    axes[1].plot(history['accuracy'], label='Обучающая', linewidth=2)
    if 'val_accuracy' in history and history['val_accuracy']:
        axes[1].plot(history['val_accuracy'], label='Валидационная', linewidth=2)
    axes[1].set_title('Точность', fontsize=14)
    axes[1].set_xlabel('Эпоха', fontsize=12)
    axes[1].set_ylabel('Точность', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_confusion_matrix(y_true, y_pred):
    """Построение матрицы ошибок"""
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    ax.set(xticks=np.arange(10),
           yticks=np.arange(10),
           xticklabels=range(10),
           yticklabels=range(10),
           title='Матрица ошибок',
           ylabel='Истинная метка',
           xlabel='Предсказанная метка')

    # Добавление чисел в ячейки
    thresh = cm.max() / 2.
    for i in range(10):
        for j in range(10):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    return fig