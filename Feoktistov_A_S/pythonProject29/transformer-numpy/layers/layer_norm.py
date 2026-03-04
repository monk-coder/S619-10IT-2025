# layer_norm.py
import numpy as np


class LayerNorm:
    def __init__(self, dim, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(dim)
        self.beta = np.zeros(dim)

        # Градиенты
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta = np.zeros_like(self.beta)

        # Для backward
        self.cache = {}

    def forward(self, x):
        """
        x: (batch_size, seq_len, dim)
        """
        self.cache['x'] = x
        self.cache['mean'] = np.mean(x, axis=-1, keepdims=True)
        self.cache['var'] = np.var(x, axis=-1, keepdims=True)
        self.cache['x_norm'] = (x - self.cache['mean']) / np.sqrt(self.cache['var'] + self.eps)

        return self.gamma * self.cache['x_norm'] + self.beta

    def backward(self, dout):
        """
        dout: (batch_size, seq_len, dim)
        """
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']

        N = x.shape[-1]

        # Градиенты для gamma и beta
        self.dgamma = np.sum(dout * x_norm, axis=(0, 1))
        self.dbeta = np.sum(dout, axis=(0, 1))

        # Градиент для входа
        dx_norm = dout * self.gamma

        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps) ** (-1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)

        dx = dx_norm / np.sqrt(var + self.eps) + \
             dvar * 2 * (x - mean) / N + \
             dmean / N

        return dx

    def get_parameters(self):
        return [(self.gamma, self.dgamma), (self.beta, self.dbeta)]

    def zero_grad(self):
        self.dgamma.fill(0)
        self.dbeta.fill(0)