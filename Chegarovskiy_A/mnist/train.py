import numpy as np
import argparse
from model import NeuralNetwork, load_mnist_data
from model import create_training_plots, save_training_report


def validate_layer_sizes(layer_string):
    try:
        sizes = [int(x.strip()) for x in layer_string.split(',')]
        
        if len(sizes) < 2:
            raise ValueError("Нужно минимум 2 слоя")
        
        if sizes[0] != 784:
            print(f"Внимание: первый слой должен быть 784, получен {sizes[0]}")
            
        if sizes[-1] != 10:
            print(f"Внимание: последний слой должен быть 10, получен {sizes[-1]}")
            
        return sizes
        
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
    
    layer_sizes = validate_layer_sizes(args.layers)
    
    print("\n[1/5] Загрузка данных...")
    train_images, train_labels, test_images, test_labels = load_mnist_data()
    
    # One-hot encoding
    train_encoded = np.eye(10)[train_labels]
    test_encoded = np.eye(10)[test_labels]
    
    validation_images = train_images[:args.val_size]
    validation_labels = train_labels[:args.val_size]
    validation_encoded = np.eye(10)[validation_labels]
    
    train_images = train_images[args.val_size:]
    train_encoded = train_encoded[args.val_size:]
    
    print(f"   Обучающих:   {train_images.shape[0]}")
    print(f"   Валидационных: {validation_images.shape[0]}")
    print(f"   Тестовых:    {test_images.shape[0]}")
    
    print("\n[2/5] Создание нейронной сети...")
    model = NeuralNetwork(
        layer_sizes=layer_sizes,
        learning_rate=args.lr,
        reg_lambda=args.reg
    )
    
    print(f"   Архитектура: {' → '.join(map(str, layer_sizes))}")
    
    print("\n[3/5] Обучение модели...")
    print("-" * 60)
    
    training_history = {
        'train_loss': [], 'val_loss': [],
        'train_acc': [], 'val_acc': []
    }
    
    for epoch in range(args.epochs):
        train_loss, train_acc = model.train_epoch(
            train_images, train_encoded, args.batch_size
        )
        
        val_loss, val_acc = model.evaluate(validation_images, validation_encoded)
        
        training_history['train_loss'].append(train_loss)
        training_history['train_acc'].append(train_acc)
        training_history['val_loss'].append(val_loss)
        training_history['val_acc'].append(val_acc)
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"   Epoch {epoch+1:3d}/{args.epochs} | "
                  f"Loss: {train_loss:.4f} | "
                  f"Train Acc: {train_acc:.2%} | "
                  f"Val Acc: {val_acc:.2%}")
    
    print("-" * 60)
    
    print("\n[4/5] Оценка на тестовых данных...")
    test_predictions = model.predict(test_images)
    test_accuracy = np.mean(test_predictions == test_labels)
    
    print(f"   Test accuracy: {test_accuracy:.2%}")
    print(f"   Correct: {np.sum(test_predictions == test_labels)}")
    print(f"   Incorrect: {np.sum(test_predictions != test_labels)}")
    
    print("\n[5/5] Сохранение результатов...")
    model.save_model('trained_model.pkl')
    
    training_params = {
        'layers': layer_sizes,
        'lr': args.lr,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'reg': args.reg,
        'val_size': args.val_size
    }
    save_training_report(training_history, test_accuracy, training_params)
    
    create_training_plots(training_history, test_labels, test_predictions)
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION")
    print("=" * 60)
    print("Первые 10 тестовых изображений:")
    
    demo_predictions = model.predict(test_images[:10])
    for i in range(10):
        status = "✓" if demo_predictions[i] == test_labels[i] else "✗"
        print(f"   Image {i+1:2d}: True = {test_labels[i]}, Predicted = {demo_predictions[i]} {status}")
    
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
