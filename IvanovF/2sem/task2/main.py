import matplotlib.pyplot as plt
import numpy as np

from nn import NeuralNetwork
from utils import load_data

EPOCHS = 10
BATCH_SIZE = 64
LEARNING_RATE = 0.1
LOSS_PLOT_PATH = "loss.png"
ACC_PLOT_PATH = "accuracy.png"


def main():
    X_train, y_train, X_test, y_test = load_data()
    model = NeuralNetwork(lr=LEARNING_RATE)

    loss_history = []
    acc_history = []

    for epoch in range(EPOCHS):
        perm = np.random.permutation(len(X_train))
        X_train = X_train[perm]
        y_train = y_train[perm]

        for i in range(0, len(X_train), BATCH_SIZE):
            X_batch = X_train[i:i + BATCH_SIZE]
            y_batch = y_train[i:i + BATCH_SIZE]

            model.forward(X_batch)
            model.backward(X_batch, y_batch)

        loss = model.compute_loss(y_train, model.forward(X_train))
        acc = model.accuracy(X_test, y_test)

        loss_history.append(loss)
        acc_history.append(acc)

        print(f"Epoch {epoch + 1}: loss={loss:.4f}, acc={acc:.4f}")

    plt.figure()
    plt.plot(loss_history)
    plt.title("Loss по эпохам")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.savefig(LOSS_PLOT_PATH)

    plt.figure()
    plt.plot(acc_history)
    plt.title("Accuracy по эпохам")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.savefig(ACC_PLOT_PATH)

    print("Итоговая точность:", acc_history[-1])


if __name__ == "__main__":
    main()