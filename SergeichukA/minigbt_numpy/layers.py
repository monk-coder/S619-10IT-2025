# layers.py — исправленная версия
import numpy as np

# ===== GELU Activation =====
def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

def gelu_backward(x):
    sqrt_2_pi = np.sqrt(2 / np.pi)
    x_sq = x * x
    x_cu = x_sq * x
    tanh_arg = sqrt_2_pi * (x + 0.044715 * x_cu)
    tanh_val = np.tanh(tanh_arg)
    sech_sq = 1 - tanh_val * tanh_val
    return 0.5 * (1 + tanh_val) + 0.5 * x * sech_sq * sqrt_2_pi * (1 + 3 * 0.044715 * x_sq)


# ===== Linear Layer =====
class Linear:
    def __init__(self, in_features, out_features, std=0.02):
        self.W = np.random.randn(in_features, out_features).astype(np.float32) * std
        self.b = np.zeros(out_features, dtype=np.float32)
        self.cache = None
        self.grads = {'W': None, 'b': None}
        self._adam_state = {}

    def forward(self, x):
        self.cache = x
        return x @ self.W + self.b

    def backward(self, grad_output):
        """Единственный метод backward — без дублирования!"""
        x = self.cache
        x_flat = x.reshape(-1, x.shape[-1])
        grad_flat = grad_output.reshape(-1, grad_output.shape[-1])
        
        self.grads['W'] = x_flat.T @ grad_flat
        self.grads['b'] = grad_flat.sum(axis=0)
        return grad_output @ self.W.T

    def update(self, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        for name, param in [('W', self.W), ('b', self.b)]:
            if name not in self._adam_state:
                self._adam_state[name] = {
                    'm': np.zeros_like(param), 
                    'v': np.zeros_like(param), 
                    't': 0
                }
            s = self._adam_state[name]
            s['t'] += 1
            g = self.grads[name]
            s['m'] = beta1 * s['m'] + (1 - beta1) * g
            s['v'] = beta2 * s['v'] + (1 - beta2) * (g * g)
            m_hat = s['m'] / (1 - beta1 ** s['t'])
            v_hat = s['v'] / (1 - beta2 ** s['t'])
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)


# ===== LayerNorm =====
class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model, dtype=np.float32)
        self.beta = np.zeros(d_model, dtype=np.float32)
        self.cache = None
        self.grads = {'gamma': None, 'beta': None}
        self._adam_state = {}

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        self.cache = (x, x_norm, mean, var)
        return x_norm * self.gamma + self.beta

    def backward(self, grad_output):
        x, x_norm, mean, var = self.cache
        self.grads['gamma'] = (grad_output * x_norm).sum(axis=(0, 1))
        self.grads['beta'] = grad_output.sum(axis=(0, 1))
        
        dx_norm = grad_output * self.gamma
        N = x.shape[-1]
        inv_std = 1.0 / np.sqrt(var + self.eps)
        dx = (inv_std / N) * (
            N * dx_norm 
            - dx_norm.sum(axis=-1, keepdims=True) 
            - x_norm * (dx_norm * x_norm).sum(axis=-1, keepdims=True)
        )
        return dx

    def update(self, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        for name, param in [('gamma', self.gamma), ('beta', self.beta)]:
            if name not in self._adam_state:
                self._adam_state[name] = {
                    'm': np.zeros_like(param), 
                    'v': np.zeros_like(param), 
                    't': 0
                }
            s = self._adam_state[name]
            s['t'] += 1
            g = self.grads[name]
            s['m'] = beta1 * s['m'] + (1 - beta1) * g
            s['v'] = beta2 * s['v'] + (1 - beta2) * (g * g)
            m_hat = s['m'] / (1 - beta1 ** s['t'])
            v_hat = s['v'] / (1 - beta2 ** s['t'])
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)


# ===== Embedding Layer =====
class Embedding:
    def __init__(self, num_embeddings, embedding_dim, std=0.02):
        self.W = np.random.randn(num_embeddings, embedding_dim).astype(np.float32) * std
        self.cache = None
        self.grads = {'W': None}
        self._adam_state = {}

    def forward(self, indices):
        self.cache = indices
        return self.W[indices]

    def backward(self, grad_output):
        self.grads['W'] = np.zeros_like(self.W)
        np.add.at(self.grads['W'], self.cache, grad_output)
        return None

    def update(self, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        if 'm' not in self._adam_state:
            self._adam_state = {
                'm': np.zeros_like(self.W), 
                'v': np.zeros_like(self.W), 
                't': 0
            }
        s = self._adam_state
        s['t'] += 1
        g = self.grads['W']
        s['m'] = beta1 * s['m'] + (1 - beta1) * g
        s['v'] = beta2 * s['v'] + (1 - beta2) * (g * g)
        m_hat = s['m'] / (1 - beta1 ** s['t'])
        v_hat = s['v'] / (1 - beta2 ** s['t'])
        self.W -= lr * m_hat / (np.sqrt(v_hat) + eps)