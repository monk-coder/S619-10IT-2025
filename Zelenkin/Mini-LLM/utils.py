import numpy as np


def softmax(x, axis=-1):
    """Численно стабильный softmax"""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def gelu(x):
    """GELU активация"""
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))


def layer_norm(x, gamma, beta, eps=1e-5):
    """Layer normalization"""
    mean = np.mean(x, axis=-1, keepdims=True)
    var = np.var(x, axis=-1, keepdims=True)
    x_centered = x - mean
    std_inv = 1.0 / np.sqrt(var + eps)
    normalized = x_centered * std_inv
    output = gamma * normalized + beta

    cache = (mean, var, x_centered, std_inv)
    return output, cache


def cross_entropy_loss(logits, targets):
    """
    logits: (batch_size, seq_len, vocab_size)
    targets: (batch_size, seq_len)
    """
    batch_size, seq_len, vocab_size = logits.shape

    # Softmax
    probs = softmax(logits.reshape(-1, vocab_size))
    probs = probs.reshape(batch_size, seq_len, vocab_size)

    # Cross-entropy
    loss = 0
    for b in range(batch_size):
        for s in range(seq_len):
            loss -= np.log(probs[b, s, targets[b, s]] + 1e-10)

    loss = loss / (batch_size * seq_len)

    # Градиент
    grad_logits = probs.copy()
    for b in range(batch_size):
        for s in range(seq_len):
            grad_logits[b, s, targets[b, s]] -= 1

    grad_logits = grad_logits / (batch_size * seq_len)

    return loss, grad_logits


class Adam:
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8):
        self.params = params
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.m = [np.zeros_like(p) for p, _ in params]
        self.v = [np.zeros_like(p) for p, _ in params]
        self.t = 0

    def step(self):
        self.t += 1
        for i, (param, grad) in enumerate(self.params):
            self.m[i] = self.betas[0] * self.m[i] + (1 - self.betas[0]) * grad
            self.v[i] = self.betas[1] * self.v[i] + (1 - self.betas[1]) * grad ** 2

            m_hat = self.m[i] / (1 - self.betas[0] ** self.t)
            v_hat = self.v[i] / (1 - self.betas[1] ** self.t)

            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        for _, grad in self.params:
            grad.fill(0)