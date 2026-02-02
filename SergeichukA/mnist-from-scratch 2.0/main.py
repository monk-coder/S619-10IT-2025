"""Точка входа: обучение MLP на MNIST с нуля"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import os

# Импорты модулей проекта
from data.loader import load_mnist
from network.mlp import MLP
from optimizers.sgd import SGD
from training.trainer import Trainer
from visualization.plots import plot_history, plot_confusion_matrix


def parse_args():
    """
    Парсинг аргументов командной строки (ранее в config.py)
    """
    parser = argparse.ArgumentParser(description='MNIST MLP Classifier (NumPy implementation)')
    
    # Гиперпараметры обучения
    parser.add_argument('--epochs', type=int, default=20,
                        help='Количество эпох обучения (по умолчанию: 20)')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Размер мини-батча (по умолчанию: 64)')
    parser.add_argument('--lr', type=float, default=0.01,
                        help='Скорость обучения (по умолчанию: 0.01)')
    parser.add_argument('--hidden', type=int, nargs='+', default=[128, 64],
                        help='Архитектура скрытых слоёв, например: --hidden 256 128 (по умолчанию: 128 64)')
    parser.add_argument('--reg', type=float, default=0.001,
                        help='Коэффициент L2-регуляризации (по умолчанию: 0.001)')
    parser.add_argument('--save_plots', action='store_true',
                        help='Сохранять графики в файлы (по умолчанию: False)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Seed для воспроизводимости (по умолчанию: 42)')
    
    # Пути для сохранения
    parser.add_argument('--output_dir', type=str, default='results',
                        help='Директория для сохранения результатов (по умолчанию: results)')
    
    return parser.parse_args()


def main():
    # Парсинг аргументов
    args = parse_args()
    
    # Фиксация случайных чисел для воспроизводимости
    np.random.seed(args.seed)
    
    # Создание директории для результатов
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("MNIST MLP CLASSIFIER (NumPy implementation)")
    print("=" * 60)
    print(f"Гиперпараметры:")
    print(f"  Эпохи:          {args.epochs}")
    print(f"  Batch size:     {args.batch_size}")
    print(f"  Learning rate:  {args.lr}")
    print(f"  Скрытые слои:   {args.hidden}")
    print(f"  L2 регуляризация: {args.reg}")
    print(f"  Seed:           {args.seed}")
    print("=" * 60)
    
    # Загрузка данных
    print("\n[1/5] Загрузка данных MNIST...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_mnist()
    print(f"  Train:   {X_train.shape[0]} образцов")
    print(f"  Val:     {X_val.shape[0]} образцов")
    print(f"  Test:    {X_test.shape[0]} образцов")
    
    # Инициализация модели
    print("\n[2/5] Инициализация модели...")
    input_size = 784  # 28x28 пикселей
    output_size = 10  # 10 классов (цифры 0-9)
    layer_sizes = [input_size] + args.hidden + [output_size]
    
    model = MLP(layer_sizes)
    print(f"  Архитектура: { ' -> '.join(map(str, layer_sizes)) }")
    
    # Инициализация оптимизатора
    print("\n[3/5] Инициализация оптимизатора SGD...")
    optimizer = SGD(model, lr=args.lr, reg=args.reg)
    
    # Обучение
    print("\n[4/5] Обучение модели...")
    trainer = Trainer(model, optimizer)
    history = trainer.fit(
        X_train, y_train,
        X_val, y_val,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    # Оценка на тестовой выборке
    print("\n[5/5] Оценка на тестовой выборке...")
    test_accuracy = model.score(X_test, y_test)
    print(f"  Тестовая точность: {test_accuracy:.4f} ({test_accuracy * 100:.2f}%)")
    
    # Подробный отчёт классификации
    y_pred = model.predict(X_test)
    print("\nОтчёт классификации (тестовая выборка):")
    print(classification_report(y_test, y_pred, digits=4))
    
    # Визуализация результатов
    print("\nГенерация визуализаций...")
    
    # График истории обучения
    plot_history(history, save_path=os.path.join(args.output_dir, 'training_history.png') if args.save_plots else None)
    
    # Матрица ошибок
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm, save_path=os.path.join(args.output_dir, 'confusion_matrix.png') if args.save_plots else None)
    
    # Сохранение модели (опционально)
    if args.save_plots:
        model_path = os.path.join(args.output_dir, 'model_weights.npz')
        model.save(model_path)
        print(f"\nМодель сохранена: {model_path}")
    
    print("\n" + "=" * 60)
    print("Обучение завершено!")
    print("=" * 60)


if __name__ == "__main__":
    main()