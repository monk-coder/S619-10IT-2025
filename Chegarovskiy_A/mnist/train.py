import numpy as np
import argparse
from typing import List
from model import NeuralNetwork, load_mnist, one_hot_encode
from model import plot_results, save_report


def validate_layers(layers_str: str) -> List[int]:
    try:
        layers = [int(x.strip()) for x in layers_str.split(',')]
        
        if len(layers) < 2:
            raise ValueError("Нужно минимум 2 слоя")
        
        if layers[0] != 784:
            print(f"Внимание: первый слой должен быть 784, получен {layers[0]}")
            
        if layers[-1] != 10:
            print(f"Внимание: последний слой должен быть 10, получен {layers[-1]}")
            
        return layers
        
    except ValueError as e:
        print(f"Ошибка в формате слоев: {e}")
        print("Пример: --layers 784,128,10")
        exit(1)


def main():
    parser = argparse.ArgumentParser(description='Обучение нейронной сети на MNIST')
    parser.add_argument('--layers', type=str, default='784,128,10',
                       help='Размеры слоев через запятую')
    parser.add_argument('--lr', type=float, default=0.01,
                       help='Learning rate')
    parser.add_argument('--epochs', type=int, default=20,
                       help='Количество эпох')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Размер батча')
    parser.add_argument('--reg', type=float, default=0.001,
                       help='L2 regularization')
    parser.add_argument('--val_size', type=int, default=5000,
                       help='Размер валидационной выборки')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    print("=" * 60)
    print("NEURAL NETWORK FOR MNIST DIGIT RECOGNITION")
    print("=" * 60)
    
    try:
        layers = validate_layers(args.layers)
    except SystemExit:
        return
    
    print("\n[1/5] Загрузка данных...")
    X_train, y_train, X_test, y_test = load_mnist()
    
    y_train_oh = one_hot_encode(y_train)
    y_test_oh = one_hot_encode(y_test)
    
    X_val = X_train[:args.val_size]
    y_val = y_train[:args.val_size]
    y_val_oh = y_train_oh[:args.val_size]
    
    X_train = X_train[args.val_size:]
    y_train = y_train[args.val_size:]
    y_train_oh = y_train_oh[args.val_size:]
    
    print(f"   Обучающих:   {X_train.shape[0]}")
    print(f"   Валидационных: {X_val.shape[0]}")
    print(f"   Тестовых:    {X_test.shape[0]}")
    
    print("\n[2/5] Создание нейронной сети...")
    model = NeuralNetwork(
        layers=layers,
        learning_rate=args.lr,
        reg_lambda=args.reg
    )
    
    print(f"   Архитектура: {' → '.join(map(str, layers))}")
    
    print("\n[3/5] Обучение модели...")
    print("-" * 60)
    
    history = {
        'train_loss': [], 'val_loss': [],
        'train_acc': [], 'val_acc': []
    }
    
    for epoch in range(args.epochs):
        train_loss, train_acc = model.train_epoch(
            X_train, y_train_oh, args.batch_size
        )
        
        val_loss, val_acc = model.evaluate(X_val, y_val_oh)
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"   Epoch {epoch+1:3d}/{args.epochs} | "
                  f"Loss: {train_loss:.4f} | "
                  f"Train Acc: {train_acc:.2%} | "
                  f"Val Acc: {val_acc:.2%}")
    
    print("-" * 60)
    
    print("\n[4/5] Оценка на тестовых данных...")
    test_predictions = model.predict(X_test)
    test_accuracy = np.mean(test_predictions == y_test)
    
    print(f"   Test accuracy: {test_accuracy:.2%}")
    print(f"   Correct: {np.sum(test_predictions == y_test)}")
    print(f"   Incorrect: {np.sum(test_predictions != y_test)}")
    
    print("\n[5/5] Сохранение результатов...")
    model.save('trained_model.pkl')
    
    params = {
        'layers': layers,
        'lr': args.lr,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'reg': args.reg,
        'val_size': args.val_size,
        'model': model
    }
    save_report(history, test_accuracy, params)
    
    plot_results(history, y_test, test_predictions)
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION")
    print("=" * 60)
    print("Первые 10 тестовых изображений:")
    
    demo_pred = model.predict(X_test[:10])
    for i in range(10):
        status = "✓" if demo_pred[i] == y_test[i] else "✗"
        print(f"   Image {i+1:2d}: True = {y_test[i]}, Predicted = {demo_pred[i]} {status}")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print("Созданы файлы:")
    print("  1. trained_model.pkl      - обученная модель")
    print("  2. report.txt            - отчет")
    print("  3. loss_accuracy.png     - графики")
    print("  4. confusion_matrix.png  - матрица ошибок")
    print("=" * 60)


if __name__ == "__main__":
    main()
