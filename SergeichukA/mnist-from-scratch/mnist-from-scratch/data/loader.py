"""Загрузка и подготовка данных MNIST"""
import numpy as np
from torchvision import datasets, transforms
from sklearn.model_selection import train_test_split

def load_mnist():
    transform = transforms.ToTensor()
    train_ds = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST('./data', train=False, download=True, transform=transform)
    
    X_train = train_ds.data.numpy().astype(np.float32).reshape(-1, 784) / 255.0
    y_train = train_ds.targets.numpy()
    X_test = test_ds.data.numpy().astype(np.float32).reshape(-1, 784) / 255.0
    y_test = test_ds.targets.numpy()
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
    )
    
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)

def one_hot(y, classes=10):
    n = y.shape[0]
    y_one = np.zeros((n, classes))
    y_one[np.arange(n), y] = 1
    return y_one