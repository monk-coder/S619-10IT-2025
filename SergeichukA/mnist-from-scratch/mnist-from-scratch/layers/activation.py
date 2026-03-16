"""Функции активации"""
import numpy as np

class ReLU:
    def forward(self, Z):
        self.Z = Z
        return np.maximum(0, Z)
    
    def backward(self, grad_output):
        return grad_output * (self.Z > 0).astype(float)

class Softmax:
    def forward(self, Z):
        exp = np.exp(Z - np.max(Z, axis=1, keepdims=True))
        self.A = exp / np.sum(exp, axis=1, keepdims=True)
        return self.A
    
    def backward(self, grad_output):
        # Градиент уже вычислен в CrossEntropyLoss
        return grad_output