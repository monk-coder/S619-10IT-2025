import numpy as np

class Module:
    def __init__(self):
        self._param_names = []
    
    def _register_param(self, name):
        self._param_names.append(name)
    
    def parameters(self):
        return {name: getattr(self, name) for name in self._param_names if hasattr(self, name)}
    
    def zero_grad(self):
        for name in self._param_names:
            grad_name = f'{name}_grad'
            if hasattr(self, grad_name):
                getattr(self, grad_name)[:] = 0

class Linear(Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        scale = np.sqrt(2.0 / (in_features + out_features))
        self.w = np.random.randn(out_features, in_features) * scale
        self.b = np.zeros((1, out_features))
        self.w_grad = np.zeros_like(self.w)
        self.b_grad = np.zeros_like(self.b)
        self._register_param('w')
        self._register_param('b')
        self.cache = None

    def forward(self, x):
        self.cache = x
        return x @ self.w.T + self.b

    def backward(self, dout):
        x = self.cache
        dout_flat = dout.reshape(-1, dout.shape[-1])
        x_flat = x.reshape(-1, x.shape[-1])
        
        self.w_grad = dout_flat.T @ x_flat
        self.b_grad = dout_flat.sum(axis=0, keepdims=True)
        
        dx = dout @ self.w
        return dx

class LayerNorm(Module):
    def __init__(self, dim, eps=1e-5):
        super().__init__()
        self.gamma = np.ones((1, 1, dim))
        self.beta = np.zeros((1, 1, dim))
        self.eps = eps
        self.gamma_grad = np.zeros_like(self.gamma)
        self.beta_grad = np.zeros_like(self.beta)
        self._register_param('gamma')
        self._register_param('beta')
        self.cache = None

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        self.cache = (x, x_norm, mean, var)
        return self.gamma * x_norm + self.beta

    def backward(self, dout):
        x, x_norm, mean, var = self.cache
        N = x.shape[-1]
        
        self.gamma_grad = (dout * x_norm).sum(axis=(0, 1), keepdims=True)
        self.beta_grad = dout.sum(axis=(0, 1), keepdims=True)
        
        dx_norm = dout * self.gamma
        dvar = (dx_norm * (x - mean) * -0.5 * (var + self.eps)**(-1.5)).sum(axis=-1, keepdims=True)
        dmean = (dx_norm * -1 / np.sqrt(var + self.eps)).sum(axis=-1, keepdims=True)
        
        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / N + dmean / N
        return dx

class MultiHeadAttention(Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        assert d_model % n_head == 0
        self.n_head = n_head
        self.d_head = d_model // n_head
        self.q_proj = Linear(d_model, d_model)
        self.k_proj = Linear(d_model, d_model)
        self.v_proj = Linear(d_model, d_model)
        self.out_proj = Linear(d_model, d_model)
        self.cache = None

    def forward(self, x, causal_mask=True):
        B, T, C = x.shape
        q = self.q_proj.forward(x)
        k = self.k_proj.forward(x)
        v = self.v_proj.forward(x)
        
        q = q.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        k = k.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        v = v.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        scores = (q @ k.transpose(0, 1, 3, 2)) / np.sqrt(self.d_head)
        
        if causal_mask:
            mask = np.triu(np.ones((T, T)), k=1) * -1e9
            scores = scores + mask
            
        attn = self.softmax(scores)
        out = attn @ v
        
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)
        out = self.out_proj.forward(out)
        
        self.cache = (q, k, v, attn, x)
        return out

    def softmax(self, x):
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def backward(self, dout):
        B, T, C = dout.shape
        q, k, v, attn, x = self.cache
        
        dout_out = self.out_proj.backward(dout)
        dout_out = dout_out.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        dv = attn.transpose(0, 1, 3, 2) @ dout_out
        dattn = dout_out @ v.transpose(0, 1, 3, 2)
        
        dscores = dattn * attn - attn * (dattn * attn).sum(axis=-1, keepdims=True)
        dscores /= np.sqrt(self.d_head)
        
        dq = dscores @ k
        dk = dscores.transpose(0, 1, 3, 2) @ q
        
        dq = dq.transpose(0, 2, 1, 3).reshape(B, T, C)
        dk = dk.transpose(0, 2, 1, 3).reshape(B, T, C)
        dv = dv.transpose(0, 2, 1, 3).reshape(B, T, C)
        
        self.q_proj.backward(dq)
        self.k_proj.backward(dk)
        self.v_proj.backward(dv)
        
        dx = dq + dk + dv
        return dx

    def zero_grad(self):
        self.q_proj.zero_grad()
        self.k_proj.zero_grad()
        self.v_proj.zero_grad()
        self.out_proj.zero_grad()

class MLP(Module):
    def __init__(self, d_model):
        super().__init__()
        self.fc1 = Linear(d_model, 4 * d_model)
        self.fc2 = Linear(4 * d_model, d_model)
        self.cache_gelu = None
        self.cache = None

    def forward(self, x):
        x = self.fc1.forward(x)
        self.cache_gelu = x
        x = self.gelu(x)
        self.cache = x
        x = self.fc2.forward(x)
        return x

    def gelu(self, x):
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

    def backward(self, dout):
        dout = self.fc2.backward(dout)
        
        x_pre_gelu = self.cache_gelu
        tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x_pre_gelu + 0.044715 * x_pre_gelu**3))
        dx = 0.5 * (1 + tanh_out) + 0.5 * x_pre_gelu * (1 - tanh_out**2) * np.sqrt(2/np.pi) * (1 + 3 * 0.044715 * x_pre_gelu**2)
        dout = dout * dx
        
        dx = self.fc1.backward(dout)
        return dx

    def zero_grad(self):
        self.fc1.zero_grad()
        self.fc2.zero_grad()

class TransformerBlock(Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model)

    def forward(self, x):
        x_norm1 = self.ln1.forward(x)
        x_attn = self.attn.forward(x_norm1)
        x = x + x_attn
        
        x_norm2 = self.ln2.forward(x)
        x_mlp = self.mlp.forward(x_norm2)
        x = x + x_mlp
        
        self.cache = (x_norm1, x_norm2)
        return x

    def backward(self, dout):
        x_norm1, x_norm2 = self.cache
        
        dout_mlp = self.mlp.backward(dout)
        dout_ln2 = self.ln2.backward(dout_mlp)
        
        dout = dout + dout_ln2
        
        dout_attn = self.attn.backward(dout)
        dout_ln1 = self.ln1.backward(dout_attn)
        
        dout = dout + dout_ln1
        
        return dout

    def zero_grad(self):
        self.ln1.zero_grad()
        self.attn.zero_grad()
        self.ln2.zero_grad()
        self.mlp.zero_grad()
