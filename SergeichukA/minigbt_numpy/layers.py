import numpy as np

def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

def gelu_backward(x):
    tanh_arg = np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)
    return 0.5 * (1 + np.tanh(tanh_arg)) + \
           0.5 * x * (1 - np.tanh(tanh_arg)**2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)

class Linear:
    def __init__(self, in_features, out_features, std=0.02):
        self.W = np.random.randn(in_features, out_features).astype(np.float32) * std
        self.b = np.zeros(out_features, dtype=np.float32)
        self.cache = None
        self.grads = {'W': None, 'b': None}
        self._adam_state = {}
        
    def backward(self, grad_output):
    x = self.cache
    # Используем einsum для эффективного вычисления градиента
    if x.ndim == 3:
        self.grads['W'] = np.einsum('bti,bto->io', x, grad_output)
        self.grads['b'] = np.sum(grad_output, axis=(0, 1))
    else:
        self.grads['W'] = x.T @ grad_output
        self.grads['b'] = np.sum(grad_output, axis=0)
    return grad_output @ self.W.T
    
    def backward(self, grad_output):
        x = self.cache
        self.grads['W'] = x.reshape(-1, x.shape[-1]).T @ grad_output.reshape(-1, grad_output.shape[-1])
        self.grads['b'] = grad_output.sum(axis=(0, 1))
        return grad_output @ self.W.T
    
    def update(self, lr):
        for name, param in [('W', self.W), ('b', self.b)]:
            if name not in self._adam_state:
                self._adam_state[name] = {'m': np.zeros_like(param), 'v': np.zeros_like(param), 't': 0}
            s = self._adam_state[name]
            s['t'] += 1
            g = self.grads[name]
            s['m'] = 0.9 * s['m'] + 0.1 * g
            s['v'] = 0.999 * s['v'] + 0.001 * g**2
            m_hat = s['m'] / (1 - 0.9**s['t'])
            v_hat = s['v'] / (1 - 0.999**s['t'])
            param -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)

class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model, dtype=np.float32)
        self.beta = np.zeros(d_model, dtype=np.float32)
        self.cache = None
        self.grads = {'gamma': None, 'beta': None}
        
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
        return (inv_std / N) * (N * dx_norm - dx_norm.sum(axis=-1, keepdims=True) - x_norm * (dx_norm * x_norm).sum(axis=-1, keepdims=True))
    
    def update(self, lr):
        self.gamma -= lr * self.grads['gamma']
        self.beta -= lr * self.grads['beta']

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
    
    def update(self, lr):
        if 'm' not in self._adam_state:
            self._adam_state = {'m': np.zeros_like(self.W), 'v': np.zeros_like(self.W), 't': 0}
        s = self._adam_state
        s['t'] += 1
        g = self.grads['W']
        s['m'] = 0.9 * s['m'] + 0.1 * g
        s['v'] = 0.999 * s['v'] + 0.001 * g**2
        m_hat = s['m'] / (1 - 0.9**s['t'])
        v_hat = s['v'] / (1 - 0.999**s['t'])
        self.W -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)
