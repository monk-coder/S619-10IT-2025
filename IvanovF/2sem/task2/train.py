
##перенесен в main



import matplotlib.pyplot as plt
from nn import NeuralNetwork
from utils import load_data
import numpy as np

X_train, y_train, X_test, y_test = load_data()

model = NeuralNetwork(lr=0.1)

epochs = 10
batch_size = 64

loss_history = []
acc_history = []

for epoch in range(epochs):
    perm = np.random.permutation(len(X_train))
    X_train = X_train[perm]
    y_train = y_train[perm]

    for i in range(0, len(X_train), batch_size):
        X_batch = X_train[i:i+batch_size]
        y_batch = y_train[i:i+batch_size]

        model.forward(X_batch)
        model.backward(X_batch, y_batch)

    loss = model.compute_loss(y_train, model.forward(X_train))
    acc = model.accuracy(X_test, y_test)

    loss_history.append(loss)
    acc_history.append(acc)

    print(f"Epoch {epoch+1}: loss={loss:.4f}, acc={acc:.4f}")

# Графики
plt.figure()
plt.plot(loss_history)
plt.title("Loss по эпохам")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.savefig("loss.png")

plt.figure()
plt.plot(acc_history)
plt.title("Accuracy по эпохам")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.savefig("accuracy.png")

print("Итоговая точность:", acc_history[-1])
