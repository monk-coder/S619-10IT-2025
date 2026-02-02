import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical

def relu(z):
    return np.maximum(0, z)

def softmax(z):
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

def forward(X, W1, b1, W2, b2):
    z1 = np.dot(X, W1) + b1
    a1 = relu(z1)
    z2 = np.dot(a1, W2) + b2
    a2 = softmax(z2)
    return a1, a2

def backward(X, y, a1, a2, W2, learning_rate):
    m = X.shape[0]
    d_z2 = a2 - y
    d_W2 = np.dot(a1.T, d_z2) / m
    d_b2 = np.sum(d_z2, axis=0, keepdims=True) / m
    d_z1 = np.dot(d_z2, W2.T) * (a1 > 0)
    d_W1 = np.dot(X.T, d_z1) / m
    d_b1 = np.sum(d_z1, axis=0, keepdims=True) / m
    return d_W1, d_b1, d_W2, d_b2

def train(X, y, epochs, learning_rate):
    input_size, hidden_size, output_size = 784, 64, 10
    W1 = np.random.randn(input_size, hidden_size) * 0.01
    b1 = np.zeros((1, hidden_size))
    W2 = np.random.randn(hidden_size, output_size) * 0.01
    b2 = np.zeros((1, output_size))
    losses = []
    accuracies = []
    for epoch in range(epochs):
        a1, output = forward(X, W1, b1, W2, b2)
        d_W1, d_b1, d_W2, d_b2 = backward(X, y, a1, output, W2, learning_rate)
        W1 -= learning_rate * d_W1
        b1 -= learning_rate * d_b1
        W2 -= learning_rate * d_W2
        b2 -= learning_rate * d_b2
        loss = -np.mean(np.sum(y * np.log(output + 1e-8), axis=1))
        acc = np.mean(np.argmax(output, axis=1) == np.argmax(y, axis=1))
        losses.append(loss)
        accuracies.append(acc)
    return W1, b1, W2, b2, losses, accuracies

def predict(X, W1, b1, W2, b2):
    _, output = forward(X, W1, b1, W2, b2)
    return np.argmax(output, axis=1)

(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train = X_train.reshape(-1, 784) / 255.0
X_test = X_test.reshape(-1, 784) / 255.0
y_train = to_categorical(y_train, 10)
y_test = to_categorical(y_test, 10)

W1, b1, W2, b2, losses, accuracies = train(X_train, y_train, epochs=5, learning_rate=0.001)

plt.plot(losses)
plt.savefig('loss.png')

plt.plot(accuracies)
plt.savefig('accuracy.png')

test_preds = predict(X_test, W1, b1, W2, b2)
test_acc = np.mean(test_preds == np.argmax(y_test, axis=1))
print(f"Test Accuracy: {test_acc:.4f}")