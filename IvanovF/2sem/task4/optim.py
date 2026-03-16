import numpy as np


class Adam:
    """Adam optimizer"""
    def __init__(self, params: dict, lr: float = 3e-4, beta1: float = 0.9, 
                 beta2: float = 0.999, eps: float = 1e-8):
        self.lr, self.beta1, self.beta2, self.eps = lr, beta1, beta2, eps
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0
        
    def step(self, params: dict, grads: dict):
        self.t += 1
        for k in params:
            if k not in grads: continue
            g = grads[k]
            self.m[k] = self.beta1 * self.m[k] + (1 - self.beta1) * g
            self.v[k] = self.beta2 * self.v[k] + (1 - self.beta2) * (g**2)
            m_hat = self.m[k] / (1 - self.beta1**self.t)
            v_hat = self.v[k] / (1 - self.beta2**self.t)
            params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class SGD:
    """SGD with momentum"""
    def __init__(self, params: dict, lr: float = 0.01, momentum: float = 0.9):
        self.lr, self.momentum = lr, momentum
        self.velocity = {k: np.zeros_like(v) for k, v in params.items()}
        
    def step(self, params: dict, grads: dict):
        for k in params:
            if k not in grads: continue
            v = self.velocity[k] = self.momentum * self.velocity[k] - self.lr * grads[k]
            params[k] += v