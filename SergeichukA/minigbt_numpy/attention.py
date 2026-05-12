import numpy as np
from utils import stable_softmax

class MultiHeadAttention:
    def __init__(self, d_model, n_heads, dropout=0.0):
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.dropout = dropout
        self.training = True
        
        self.W_q = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
        self.W_k = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
        self.W_v = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
        self.W_o = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
        
        self.cache = {}
        self.grads = {}
        self._adam_states = {}

    def forward(self, x, mask):
        B, T, C = x.shape
        self.cache['x'] = x
        
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        self.cache['Q'] = Q.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        self.cache['K'] = K.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        self.cache['V'] = V.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        
        scores = (self.cache['Q'] @ self.cache['K'].transpose(0, 1, 3, 2)) / np.sqrt(self.d_head)
        scores += mask
        attn = stable_softmax(scores, axis=-1)
        self.cache['attn'] = attn
        self.cache['mask'] = mask
        
        if self.dropout > 0 and self.training:
            drop_mask = (np.random.rand(*attn.shape) > self.dropout).astype(np.float32)
            attn = attn * drop_mask / (drop_mask.mean() + 1e-8)
            
        out_h = attn @ self.cache['V']
        out = out_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        self.cache['out_pre_o'] = out
        return out @ self.W_o
    
    def backward(self, grad_output):
        B, T, C = grad_output.shape
        Q_h, K_h, V_h = self.cache['Q'], self.cache['K'], self.cache['V']
        attn, mask, x, out_pre_o = self.cache['attn'], self.cache['mask'], self.cache['x'], self.cache['out_pre_o']
        
        # 1. Output projection
        self.grads['W_o'] = out_pre_o.reshape(-1, C).T @ grad_output.reshape(-1, C)
        grad_pre_o = grad_output @ self.W_o.T
        grad_h = grad_pre_o.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        
        # 2. Attention grads
        grad_V_h = attn.transpose(0, 1, 3, 2) @ grad_h
        grad_attn = grad_h @ V_h.transpose(0, 1, 3, 2)
        
        # Softmax backward
        grad_scores = attn * (grad_attn - np.sum(grad_attn * attn, axis=-1, keepdims=True))
        grad_scores = np.where(mask > -1e8, grad_scores, 0.0)
        
        grad_Q_h = grad_scores @ K_h / np.sqrt(self.d_head)
        grad_K_h = grad_scores.transpose(0, 1, 3, 2) @ Q_h / np.sqrt(self.d_head)
        
        # Reshape back
        grad_Q = grad_Q_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        grad_K = grad_K_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        grad_V = grad_V_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        
        # 3. Projection grads
        self.grads['W_q'] = x.reshape(-1, C).T @ grad_Q.reshape(-1, C)
        self.grads['W_k'] = x.reshape(-1, C).T @ grad_K.reshape(-1, C)
        self.grads['W_v'] = x.reshape(-1, C).T @ grad_V.reshape(-1, C)
        
        return grad_Q @ self.W_q.T + grad_K @ self.W_k.T + grad_V @ self.W_v.T
    
    def update(self, lr):
        for name in ['W_q', 'W_k', 'W_v', 'W_o']:
            if name not in self._adam_states:
                self._adam_states[name] = {'m': np.zeros_like(getattr(self, name)), 'v': np.zeros_like(getattr(self, name)), 't': 0}
            s = self._adam_states[name]
            s['t'] += 1
            g = self.grads[name]
            s['m'] = 0.9 * s['m'] + 0.1 * g
            s['v'] = 0.999 * s['v'] + 0.001 * g**2
            m_hat = s['m'] / (1 - 0.9**s['t'])
            v_hat = s['v'] / (1 - 0.999**s['t'])
            setattr(self, name, getattr(self, name) - lr * m_hat / (np.sqrt(v_hat) + 1e-8))