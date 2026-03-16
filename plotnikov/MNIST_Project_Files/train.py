import numpy as np
from mnist_nn import NeuralNetwork, load_mnist, create_validation

def train():
    print("Обучение модели...")
    
    # Загрузка данных
    data = load_mnist()
    if data is None:
        return
    
    X_train, y_train, X_test, y_test, _ = data
    
    # Валидация
    X_train, y_train, X_val, y_val = create_validation(X_train, y_train, 0.1)
    
    # Создание модели
    model = NeuralNetwork(
        layer_sizes=[784, 256, 128, 10],
        learning_rate=0.05,
        reg_lambda=0.001
    )
    
    # Обучение
    model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=128
    )
    
    # Оценка
    _, acc = model.evaluate(X_test, y_test)
    print(f"\nТочность на тесте: {acc*100:.2f}%")
    
    # Сохранение
    model.save('trained_model.pkl')

if __name__ == "__main__":
    train()