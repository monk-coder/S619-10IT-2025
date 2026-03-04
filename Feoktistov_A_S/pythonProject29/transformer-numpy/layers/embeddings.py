import numpy as np


class TokenEmbedding:
    def __init__(self, vocab_size, d_model):
        self.vocab_size = vocab_size
        self.d_model = d_model
        scale = 1 / np.sqrt(d_model)
        self.W = np.random.randn(vocab_size, d_model) * scale
        self.dW = np.zeros_like(self.W)
        self.cache = {}

    def forward(self, x):
        """x: (batch_size, seq_len) - индексы токенов"""
        self.cache['x'] = x
        return self.W[x]

    def backward(self, dout):
        """dout: (batch_size, seq_len, d_model)"""
        x = self.cache['x']
        B, T = x.shape

        # Аккумулируем градиенты для каждого токена
        for b in range(B):
            for t in range(T):
                self.dW[x[b, t]] += dout[b, t]

        return dout

    def get_parameters(self):
        return [(self.W, self.dW)]

    def zero_grad(self):
        self.dW.fill(0)


class PositionalEmbedding:
    def __init__(self, max_seq_len, d_model):
        self.max_seq_len = max_seq_len
        self.d_model = d_model
        scale = 1 / np.sqrt(d_model)
        self.W = np.random.randn(max_seq_len, d_model) * scale
        self.dW = np.zeros_like(self.W)
        self.cache = {}

    def forward(self, T):
        """T: длина последовательности"""
        self.cache['T'] = T
        return self.W[:T].reshape(1, T, self.d_model)

    def backward(self, dout):
        """dout: (batch_size, T, d_model)"""
        T = self.cache['T']
        self.dW[:T] += np.sum(dout, axis=0)
        return dout

    def get_parameters(self):
        return [(self.W, self.dW)]

    def zero_grad(self):
        self.dW.fill(0)