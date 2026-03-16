import numpy as np

def cross_entropy_loss(logits, targets):
    """
    logits: (batch_size, seq_len, vocab_size)
    targets: (batch_size, seq_len)
    """
    B, T, V = logits.shape
    logits_flat = logits.reshape(-1, V)
    targets_flat = targets.reshape(-1)

    logits_max = np.max(logits_flat, axis=-1, keepdims=True)
    logits_stable = logits_flat - logits_max
    exp_logits = np.exp(logits_stable)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    correct_log_probs = -np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-10)
    loss = np.mean(correct_log_probs)

    dlogits = probs.copy()
    dlogits[np.arange(len(targets_flat)), targets_flat] -= 1
    dlogits = dlogits / (B * T)
    dlogits = dlogits.reshape(B, T, V)

    return loss, dlogits

def compute_accuracy(logits, targets):
    """
    logits: (batch_size, seq_len, vocab_size)
    targets: (batch_size, seq_len)
    """
    preds = np.argmax(logits, axis=-1)
    correct = (preds == targets).sum()
    total = targets.size
    return correct / total

class Optimizer:
    def __init__(self, params, lr=0.001):
        self.params = params
        self.lr = lr

    def step(self, grads):
        raise NotImplementedError

    def zero_grad(self):
        for p in self.params.values():
            p.grad.fill(0)

class SGD(Optimizer):
    def __init__(self, params, lr=0.001, momentum=0.9):
        super().__init__(params, lr)
        self.momentum = momentum
        self.velocities = {k: np.zeros_like(v) for k, v in params.items()}

    def step(self, grads):
        for k in self.params:
            if k in grads:
                self.velocities[k] = self.momentum * self.velocities[k] - self.lr * grads[k]
                self.params[k] += self.velocities[k]

class Adam(Optimizer):
    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        super().__init__(params, lr)
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0

    def step(self, grads):
        self.t += 1
        for k in self.params:
            if k in grads:
                self.m[k] = self.beta1 * self.m[k] + (1 - self.beta1) * grads[k]
                self.v[k] = self.beta2 * self.v[k] + (1 - self.beta2) * (grads[k] ** 2)
                m_hat = self.m[k] / (1 - self.beta1 ** self.t)
                v_hat = self.v[k] / (1 - self.beta2 ** self.t)
                self.params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)