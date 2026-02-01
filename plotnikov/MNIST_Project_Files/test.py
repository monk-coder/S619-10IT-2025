import numpy as np
import matplotlib.pyplot as plt
from mnist_nn import NeuralNetwork, load_mnist

def test(model_file='trained_model.pkl'):
    print(f"Тестирование модели из {model_file}")
    
    try:
        model = NeuralNetwork.load(model_file)
    except:
        print("Модель не найдена. Сначала запустите train.py")
        return
    
    # Данные
    data = load_mnist()
    if data is None:
        return
    
    _, _, X_test, y_test, y_test_labels = data
    
    # Оценка
    loss, acc = model.evaluate(X_test, y_test)
    print(f"\nТочность: {acc*100:.2f}%\nПотери: {loss:.4f}")
    
    # Примеры
    print("\nПримеры предсказаний:")
    fig, axes = plt.subplots(2, 5, figsize=(12, 5))
    
    for i, ax in enumerate(axes.flat):
        sample = X_test[i:i+1]
        pred, _ = model.predict(sample)
        true = y_test_labels[i]
        
        img = sample.reshape(28, 28)
        ax.imshow(img, cmap='gray')
        ax.axis('off')
        
        color = 'green' if pred[0] == true else 'red'
        ax.set_title(f"True: {true}\nPred: {pred[0]}", color=color)
    
    plt.suptitle("Примеры предсказаний", fontsize=14)
    plt.tight_layout()
    plt.savefig('predictions.png', dpi=150, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    test()