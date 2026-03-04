# mlp.py
import numpy as np
from utils import gelu, gelu_derivative


class MLP:
    def __init__(self, d_model, d_ff):
        self.d_model = d_model
        self.d_ff = d_ff

        # Веса (Xavier инициализация)
        scale1 = 1 / np.sqrt(d_model)
        scale2 = 1 / np.sqrt(d_ff)

        self.W1 = np.random.randn(d_model, d_ff) * scale1
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * scale2
        self.b2 = np.zeros(d_model)

        # Градиенты
        self.dW1 = np.zeros_like(self.W1)
        self.db1 = np.zeros_like(self.b1)
        self.dW2 = np.zeros_like(self.W2)
        self.db2 = np.zeros_like(self.b2)

        self.cache = {}

    def forward(self, x):
        """
        x: (batch_size, seq_len, d_model)
        """
        self.cache['x'] = x

        # Первый линейный слой + GELU
        hidden = x @ self.W1 + self.b1  # (B, T, d_ff)
        self.cache['hidden'] = hidden
        self.cache['activation'] = gelu(hidden)

        # Второй линейный слой
        output = self.cache['activation'] @ self.W2 + self.b2

        return output

    def backward(self, dout):
        """
        dout: (batch_size, seq_len, d_model)
        """
        x = self.cache['x']
        hidden = self.cache['hidden']
        activation = self.cache['activation']

        B, T, _ = dout.shape

        # Градиенты для второго слоя
        self.dW2 = activation.reshape(-1, self.d_ff).T @ dout.reshape(-1, self.d_model)
        self.db2 = np.sum(dout, axis=(0, 1))

        # Градиент для activation
        dactivation = dout @ self.W2.T  # (B, T, d_ff)

        # Градиент для hidden (обратно через GELU)
        dhidden = dactivation * gelu_derivative(hidden)

        # Градиенты для первого слоя
        self.dW1 = x.reshape(-1, self.d_model).T @ dhidden.reshape(-1, self.d_ff)
        self.db1 = np.sum(dhidden, axis=(0, 1))

        # Градиент для входа
        dx = dhidden @ self.W1.T

        return dx

    def get_parameters(self):
        params = [
            (self.W1, self.dW1),
            (self.b1, self.db1),
            (self.W2, self.dW2),
            (self.b2, self.db2)
        ]
        return params

    def zero_grad(self):
        self.dW1.fill(0)
        self.db1.fill(0)
        self.dW2.fill(0)
        self.db2.fill(0)