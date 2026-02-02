"""Функции активации"""
import numpy as np

class ReLU:
    def __init__(self):
        self.Z = None  # Явное объявление атрибута до использования
    
    def forward(self, Z):
        self.Z = Z  # Сохранение входа для backward
        return np.maximum(0, Z)
    
    def backward(self, grad_output):
        return grad_output * (self.Z > 0).astype(float)

class Softmax:
    def __init__(self):
        self.A = None  # Активации (выход слоя)
        self.Z = None  # Явное объявление входа для единообразия
    
    def forward(self, Z):
        self.Z = Z  # Сохранение входа (хотя в backward обычно не используется)
        exp = np.exp(Z - np.max(Z, axis=1, keepdims=True))
        self.A = exp / np.sum(exp, axis=1, keepdims=True)
        return self.A
    
    def backward(self, grad_output):
        # Градиент уже вычислен в связке с CrossEntropyLoss
        # (численно стабильная реализация объединяет softmax + кросс-энтропию)
        return grad_output