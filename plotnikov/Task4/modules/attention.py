import numpy as np

class MultiHeadCausalAttention:
    def __init__(self, d_model, n_head, max_len=512, seed=42):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_model // n_head
        
        rng = np.random.default_rng(seed)
        scale = 0.02
        self.W_q = rng.normal(0, scale, (d_model, d_model)).astype(np.float32)
        self.W_k = rng.normal(0, scale, (d_model, d_model)).astype(np.float32)
        self.W_v = rng.normal(0, scale, (d_model, d_model)).astype(np.float32)
        self.W_o = rng.normal(0, scale, (d_model, d_model)).astype(np.float32)
        
        self.grad_W_q = np.zeros_like(self.W_q)
        self.grad_W_k = np.zeros_like(self.W_k)
        self.grad_W_v = np.zeros_like(self.W_v)
        self.grad_W_o = np.zeros_like(self.W_o)

    def _create_causal_mask(self, T):
        mask = np.triu(np.ones((T, T)), k=1) * -1e9
        return mask

    def forward(self, x):
        B, T, _ = x.shape
        self.B, self.T = B, T
        self.x = x
        
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        def split_heads(tensor):
            return tensor.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        Q_h = split_heads(Q)
        K_h = split_heads(K)
        V_h = split_heads(V)
        
        scores = Q_h @ K_h.transpose(0, 1, 3, 2) / np.sqrt(self.d_head)
        causal_mask = self._create_causal_mask(T)
        scores = scores + causal_mask[None, None, :, :]
        
        exp_scores = np.exp(scores - scores.max(axis=-1, keepdims=True))
        self.attn_weights = exp_scores / (exp_scores.sum(axis=-1, keepdims=True) + 1e-8)
        
        out_h = self.attn_weights @ V_h
        out = out_h.transpose(0, 2, 1, 3).reshape(B, T, -1)
        
        self.V_h = V_h
        self.Q_h = Q_h
        self.K_h = K_h
        return out @ self.W_o

    def backward(self, grad_output):
        B, T, _ = grad_output.shape
        out = self.attn_weights @ self.V_h
        out = out.transpose(0, 2, 1, 3).reshape(B, T, -1)
        self.grad_W_o += out.T @ grad_output
        
        d_out = grad_output @ self.W_o.T
        d_out_h = d_out.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        d_V_h = self.attn_weights.transpose(0, 1, 3, 2) @ d_out_h
        d_attn_weights = d_out_h @ self.V_h.transpose(0, 1, 3, 2)
        
        s = self.attn_weights
        d_scores = d_attn_weights * s - s * (d_attn_weights * s).sum(axis=-1, keepdims=True)
        
        causal_mask = self._create_causal_mask(T)
        d_scores = d_scores * (causal_mask[None, None, :, :] == 0).astype(np.float32)
        d_scores /= np.sqrt(self.d_head)
        
        d_Q_h = d_scores @ self.K_h
        d_K_h = d_scores.transpose(0, 1, 3, 2) @ self.Q_h
        
        d_Q = d_Q_h.transpose(0, 2, 1, 3).reshape(B, T, -1)
        d_K = d_K_h.transpose(0, 2, 1, 3).reshape(B, T, -1)
        d_V = d_V_h.transpose(0, 2, 1, 3).reshape(B, T, -1)
        
        x_flat = self.x.reshape(-1, self.d_model)
        self.grad_W_q += x_flat.T @ d_Q.reshape(-1, self.d_model)
        self.grad_W_k += x_flat.T @ d_K.reshape(-1, self.d_model)
        self.grad_W_v += x_flat.T @ d_V.reshape(-1, self.d_model)
        
        return d_Q @ self.W_q.T + d_K @ self.W_k.T + d_V @ self.W_v.T

    def zero_grad(self):
        self.grad_W_q.fill(0)
        self.grad_W_k.fill(0)
        self.grad_W_v.fill(0)
        self.grad_W_o.fill(0)