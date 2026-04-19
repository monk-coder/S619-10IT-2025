import numpy as np
from tensorflow.keras.datasets import mnist

NORMALIZATION_FACTOR = 255.0


def load_data():
    (X_train, y_train), (X_test, y_test) = mnist.load_data()

    X_train = X_train.reshape(-1, 784) / NORMALIZATION_FACTOR
    X_test = X_test.reshape(-1, 784) / NORMALIZATION_FACTOR

    return X_train, y_train, X_test, y_test