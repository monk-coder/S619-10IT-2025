import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist

(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(-1, 784) / 255
X_test = X_test.reshape(-1, 784) / 255

def one_hot(y):
    result = np.zeros((len(y), 10))
    for i in range(len(y)):
        result[i][y[i]] = 1
    return result

Y_train = one_hot(y_train)
Y_test = one_hot(y_test)

weights = np.random.randn(784, 10) * 0.01
bias = np.zeros((1, 10))

learning_rate = 0.1

def softmax(x):
    exp = np.exp(x)
    return exp / np.sum(exp, axis=1, keepdims=True)

def predict(x):
    z = x @ weights + bias
    return softmax(z)

def accuracy(x, y):
    p = predict(x)
    answers = np.argmax(p, axis=1)
    true = np.argmax(y, axis=1)
    return np.mean(answers == true)

loss_history = []
acc_history = []

for epoch in range(5):

    z = X_train @ weights + bias
    out = softmax(z)

    loss = -np.mean(Y_train * np.log(out + 0.0001))

    error = out - Y_train

    dW = X_train.T @ error / len(X_train)
    dB = np.mean(error, axis=0, keepdims=True)

    weights = weights - learning_rate * dW
    bias = bias - learning_rate * dB

    acc = accuracy(X_test, Y_test)

    loss_history.append(loss)
    acc_history.append(acc)

    print(epoch+1, loss, acc)

plt.plot(loss_history)
plt.savefig("loss.png")
plt.clf()

plt.plot(acc_history)
plt.savefig("accuracy.png")

print(acc_history[-1])
