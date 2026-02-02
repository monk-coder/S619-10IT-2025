"""Полносвязная нейросеть с прямым и обратным распространением"""
import numpy as np
from layers.linear import Linear
from layers.activation import ReLU, Softmax
from loss.cross_entropy import CrossEntropyLoss

class MLP:
    def __init__(self, layer_sizes, reg_lambda=0.001):
        self.layers = []
        self.reg_lambda = reg_lambda
        
        for i in range(len(layer_sizes) - 2):
            self.layers.append(Linear(layer_sizes[i], layer_sizes[i+1]))
            self.layers.append(ReLU())
        
        self.layers.append(Linear(layer_sizes[-2], layer_sizes[-1]))
        self.layers.append(Softmax())
        self.loss_fn = CrossEntropyLoss()
    
    def forward(self, X):
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A
    
    def backward(self, y_pred, y_true):
        grad = self.loss_fn.grad(y_pred, y_true)
        # Передаём регуляризацию ТОЛЬКО линейным слоям
        for layer in reversed(self.layers):
            if hasattr(layer, 'W'):  # Linear layer
                grad = layer.backward(grad, self.reg_lambda)
            else:  # Activation layer (ReLU/Softmax)
                grad = layer.backward(grad)
        return grad
    
    def loss(self, y_pred, y_true):
        data_loss = self.loss_fn(y_pred, y_true)
        reg_loss = sum(np.sum(layer.W ** 2) for layer in self.layers if hasattr(layer, 'W'))
        reg_loss = 0.5 * self.reg_lambda * reg_loss / y_true.shape[0]
        return data_loss + reg_loss
    
    def predict(self, X):
        probs = self.forward(X)
        return np.argmax(probs, axis=1)
    
    def score(self, X, y):
        return np.mean(self.predict(X) == y)