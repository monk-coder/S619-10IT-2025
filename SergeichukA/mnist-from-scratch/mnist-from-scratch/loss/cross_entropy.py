"""Кросс-энтропия с объединенным градиентом для softmax"""
import numpy as np

class CrossEntropyLoss:
    def __call__(self, y_pred, y_true):
        n = y_true.shape[0]
        log_probs = -np.log(np.maximum(y_pred[range(n), y_true.argmax(axis=1)], 1e-15))
        return np.sum(log_probs) / n
    
    def grad(self, y_pred, y_true):
        """Объединенный градиент для softmax + cross-entropy"""
        n = y_true.shape[0]
        grad = y_pred.copy()
        grad[range(n), y_true.argmax(axis=1)] -= 1
        return grad / n