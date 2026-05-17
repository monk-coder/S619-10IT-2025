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
        
        # Xavier initialization для лучшей сходимости
        scale = 1 / np.sqrt(d_model)
        self.W_q = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_k = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_v = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_o = np.random.randn(d_model, d_model).astype(np.float32) * scale
        
        self.cache = {}
        self.grads = {}
        self._adam_state = {}

    def forward(self, x, mask):
        B, T, C = x.shape
        self.cache['x'] = x
        self.cache['B'], self.cache['T'] = B, T
        
        # Проекции
        Q = x @ self.W_q
        K = x @ self.W_k  
        V = x @ self.W_v
        
        # Reshape для multi-head: (B, n_heads, T, d_head)
        def split_heads(tensor):
            return tensor.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        
        Q_h = split_heads(Q)
        K_h = split_heads(K)
        V_h = split_heads(V)
        
        self.cache['Q_h'], self.cache['K_h'], self.cache['V_h'] = Q_h, K_h, V_h
        
        # Scaled dot-product attention
        scores = (Q_h @ K_h.transpose(0, 1, 3, 2)) * (1.0 / np.sqrt(self.d_head))
        scores = scores + mask  # mask уже содержит -1e9 для padding
        
        attn = stable_softmax(scores, axis=-1)
        self.cache['attn'] = attn
        
        # Dropout только в training
        if self.dropout > 0 and self.training:
            mask_drop = (np.random.rand(*attn.shape) > self.dropout).astype(np.float32)
            attn = attn * mask_drop / (mask_drop.mean() + 1e-8)
        
        # Выход
        out_h = attn @ V_h
        out = out_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        self.cache['out_pre_o'] = out
        
        return out @ self.W_o

    def backward(self, grad_output):
        B, T, C = grad_output.shape
        Q_h = self.cache['Q_h']
        K_h = self.cache['K_h'] 
        V_h = self.cache['V_h']
        attn = self.cache['attn']
        x = self.cache['x']
        out_pre_o = self.cache['out_pre_o']
        
        # 1. Градиент через выходную проекцию
        self.grads['W_o'] = out_pre_o.reshape(-1, C).T @ grad_output.reshape(-1, C)
        grad_pre_o = grad_output @ self.W_o.T
        grad_h = grad_pre_o.reshape(B, T, self.n_heads, self.d_head).transpose(0, 2, 1, 3)
        
        # 2. Градиенты внимания
        grad_V_h = attn.transpose(0, 1, 3, 2) @ grad_h
        grad_attn_raw = grad_h @ V_h.transpose(0, 1, 3, 2)
        
        # Softmax backward: аттеншн * (grad - sum(grad * attn))
        grad_attn = attn * (grad_attn_raw - (grad_attn_raw * attn).sum(axis=-1, keepdims=True))
        
        # 3. Градиенты по Q, K, V
        grad_Q_h = (grad_attn @ K_h) * (1.0 / np.sqrt(self.d_head))
        grad_K_h = (grad_attn.transpose(0, 1, 3, 2) @ Q_h) * (1.0 / np.sqrt(self.d_head))
        
        # Reshape back to (B, T, C)
        def combine_heads(grad_h):
            return grad_h.transpose(0, 2, 1, 3).reshape(B, T, C)
        
        grad_Q = combine_heads(grad_Q_h)
        grad_K = combine_heads(grad_K_h)
        grad_V = combine_heads(grad_V_h)
        
        # 4. Градиенты проекционных матриц
        x_flat = x.reshape(-1, C)
        self.grads['W_q'] = x_flat.T @ grad_Q.reshape(-1, C)
        self.grads['W_k'] = x_flat.T @ grad_K.reshape(-1, C)
        self.grads['W_v'] = x_flat.T @ grad_V.reshape(-1, C)
        
        # Градиент на вход
        return (grad_Q @ self.W_q.T + grad_K @ self.W_k.T + grad_V @ self.W_v.T)

    def update(self, lr, **adam_kwargs):
        for name in ['W_q', 'W_k', 'W_v', 'W_o']:
            if name not in self._adam_state:
                self._adam_state[name] = {
                    'm': np.zeros_like(getattr(self, name)),
                    'v': np.zeros_like(getattr(self, name)),
                    't': 0
                }
            s = self._adam_state[name]
            s['t'] += 1
            g = self.grads[name]
            beta1, beta2, eps = adam_kwargs.get('beta1', 0.9), adam_kwargs.get('beta2', 0.999), adam_kwargs.get('eps', 1e-8)
            
            s['m'] = beta1 * s['m'] + (1 - beta1) * g
            s['v'] = beta2 * s['v'] + (1 - beta2) * (g * g)
            m_hat = s['m'] / (1 - beta1 ** s['t'])
            v_hat = s['v'] / (1 - beta2 ** s['t'])
            
            param = getattr(self, name)
            setattr(self, name, param - lr * m_hat / (np.sqrt(v_hat) + eps))