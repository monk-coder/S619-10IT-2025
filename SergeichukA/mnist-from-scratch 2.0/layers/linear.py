"""Линейный слой с инициализацией весов"""
import numpy as np

class Linear:
    def __init__(self, in_features, out_features):
        std = np.sqrt(2.0 / in_features)
        self.W = np.random.randn(in_features, out_features) * std
        self.b = np.zeros((1, out_features))
        self.grad_W = None
        self.grad_b = None
    
    def forward(self, X):
        self.X = X
        return X @ self.W + self.b
    
    def backward(self, grad_output, reg_lambda=0.0):
        n = self.X.shape[0]
        self.grad_W = self.X.T @ grad_output / n + reg_lambda * self.W / n
        self.grad_b = np.sum(grad_output, axis=0, keepdims=True) / n
        return grad_output @ self.W.T