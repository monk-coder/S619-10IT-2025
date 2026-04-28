import numpy as np

class TokenEmbedding:
    def __init__(self, vocab_size, d_model, seed=42):
        rng = np.random.default_rng(seed)
        self.weight = rng.normal(0, 0.02, (vocab_size, d_model)).astype(np.float32)
        self.grad = np.zeros_like(self.weight)

    def forward(self, x):
        self.x = x
        return self.weight[x]

    def backward(self, grad_output):
        np.add.at(self.grad, self.x, grad_output)

    def zero_grad(self):
        self.grad.fill(0)

class PositionalEmbedding:
    def __init__(self, max_len, d_model, seed=42):
        rng = np.random.default_rng(seed)
        self.weight = rng.normal(0, 0.02, (max_len, d_model)).astype(np.float32)
        self.grad = np.zeros_like(self.weight)

    def forward(self, T):
        return self.weight[:T]

    def backward(self, grad_output, T):
        self.grad[:T] += grad_output.mean(axis=0)

    def zero_grad(self):
        self.grad.fill(0)