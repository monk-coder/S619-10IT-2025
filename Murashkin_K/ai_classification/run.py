import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from neural_network import SimpleNeuralNetwork


def load_data():
    print("Загрузка датасета MNIST...")
    # Загружаем данные через sklearn
    mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
    X, y = mnist.data, mnist.target.astype(int)

    X = X / 255.0

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train.T, X_test.T, y_train, y_test


def train_model():
    X_train, X_test, y_train, y_test = load_data()
    print(f"Размер обучающей выборки: {X_train.shape}")
    print(f"Размер тестовой выборки: {X_test.shape}")

    INPUT_SIZE = 784  # 28x28
    HIDDEN_SIZE = 128
    OUTPUT_SIZE = 10
    LEARNING_RATE = 0.1
    EPOCHS = 200

    nn = SimpleNeuralNetwork(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE, LEARNING_RATE)

    history_loss = []
    history_acc = []

    print("\nНачало обучения...")
    for i in range(EPOCHS):
        A2, cache = nn.forward_propagation(X_train)

        grads = nn.backward_propagation(X_train, y_train, cache)

        nn.update_params(grads)

        if i % 10 == 0:
            loss = nn.compute_loss(A2, y_train)
            predictions = nn.get_predictions(A2)
            acc = nn.get_accuracy(predictions, y_train)

            history_loss.append(loss)
            history_acc.append(acc)
            print(f"Epoch {i}: Loss = {loss:.4f}, Accuracy = {acc:.2%}")

    print("\nОценка на тестовых данных...")
    A2_test, _ = nn.forward_propagation(X_test)
    test_predictions = nn.get_predictions(A2_test)
    test_acc = nn.get_accuracy(test_predictions, y_test)
    print(f"Финальная точность на тесте: {test_acc:.2%}")

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(range(0, EPOCHS, 10), history_loss, label='Training Loss')
    plt.title('Loss graphic')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(range(0, EPOCHS, 10), history_acc, color='orange', label='Accuracy')
    plt.title('Accuracy graphic')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":

    train_model()
