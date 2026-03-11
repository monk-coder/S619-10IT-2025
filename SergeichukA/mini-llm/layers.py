import numpy as np

class Module:
    def parameters(self):
        return {name: val for name, val in self.__dict__.items() if isinstance(val, np.ndarray)}
    
    def zero_grad(self):
        for name, param in self.parameters().items():
            if hasattr(self, f'{name}_grad'):
                getattr(self, f'{name}_grad')[:] = 0

class Linear(Module):
    def __init__(self, in_features, out_features):
        scale = np.sqrt(2.0 / (in_features + out_features))
        self.w = np.random.randn(out_features, in_features) * scale
        self.b = np.zeros((1, out_features))
        self.w_grad = np.zeros_like(self.w)
        self.b_grad = np.zeros_like(self.b)
        self.cache = None

    def forward(self, x):
        # x: (B, T, C_in)
        self.cache = x
        return x @ self.w.T + self.b

    def backward(self, dout):
        # dout: (B, T, C_out)
        x = self.cache
        self.w_grad = dout.transpose(0, 1, 2) @ x # (B, T, Out) -> (Out, B*T) @ (B*T, In) -> (Out, In) -- Wait shapes
        # Correct shapes:
        # x: (B, T, In). dout: (B, T, Out).
        # We need sum over B, T.
        # dw = dout.T @ x
        # Reshape for matmul:
        dout_flat = dout.reshape(-1, dout.shape[-1]) # (B*T, Out)
        x_flat = x.reshape(-1, x.shape[-1]) # (B*T, In)
        
        self.w_grad = dout_flat.T @ x_flat
        self.b_grad = dout_flat.sum(axis=0, keepdims=True)
        
        dx = dout @ self.w # (B, T, Out) @ (Out, In) -> (B, T, In)
        return dx

class LayerNorm(Module):
    def __init__(self, dim, eps=1e-5):
        self.gamma = np.ones((1, 1, dim))
        self.beta = np.zeros((1, 1, dim))
        self.eps = eps
        self.gamma_grad = np.zeros_like(self.gamma)
        self.beta_grad = np.zeros_like(self.beta)
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
        dmean = (dx_norm * -1 / np.sqrt(var + self.eps)).sum(axis=-1, keepdims=True) + \
                dvar * (-2 * (x - mean).mean(axis=-1, keepdims=True))
        
        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / N + dmean / N
        return dx

class MultiHeadAttention(Module):
    def __init__(self, d_model, n_head):
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
        q = self.q_proj.forward(x) # (B, T, C)
        k = self.k_proj.forward(x)
        v = self.v_proj.forward(x)
        
        # Reshape for heads: (B, T, n_head, d_head) -> (B, n_head, T, d_head)
        q = q.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        k = k.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        v = v.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        # Attention scores
        scores = (q @ k.transpose(0, 1, 3, 2)) / np.sqrt(self.d_head) # (B, h, T, T)
        
        if causal_mask:
            mask = np.triu(np.ones((T, T)), k=1) * -1e9
            scores = scores + mask
            
        attn = self.softmax(scores)
        out = attn @ v # (B, h, T, d_head)
        
        # Concatenate heads
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)
        out = self.out_proj.forward(out)
        
        self.cache = (q, k, v, attn, scores)
        return out

    def softmax(self, x):
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def backward(self, dout):
        B, T, C = dout.shape
        q, k, v, attn, scores = self.cache
        
        # Backprop through out_proj
        dout = self.out_proj.backward(dout)
        dout = dout.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3) # (B, h, T, d_head)
        
        # Backprop through attn @ v
        dv = attn.transpose(0, 1, 3, 2) @ dout # (B, h, d_head, T) @ (B, h, T, d_head) -> (B, h, T, d_head)
        dattn = dout @ v.transpose(0, 1, 3, 2) # (B, h, T, d_head) @ (B, h, d_head, T) -> (B, h, T, T)
        
        # Backprop through softmax
        dscores = dattn * attn * (1 - attn) # Simplified softmax grad (assuming standard softmax)
        # Correct softmax grad: dscores = dattn * attn - attn * (dattn * attn).sum(-1, keepdims)
        dscores = dattn * attn - attn * (dattn * attn).sum(axis=-1, keepdims=True)
        dscores /= np.sqrt(self.d_head)
        
        # Backprop through q @ k.T
        dq = dscores @ k # (B, h, T, T) @ (B, h, T, d_head) -> (B, h, T, d_head)
        dk = dscores.transpose(0, 1, 3, 2) @ q
        
        # Reshape back to (B, T, C)
        dq = dq.transpose(0, 2, 1, 3).reshape(B, T, C)
        dk = dk.transpose(0, 2, 1, 3).reshape(B, T, C)
        dv = dv.transpose(0, 2, 1, 3).reshape(B, T, C)
        
        # Backprop through projections
        self.q_proj.backward(dq)
        self.k_proj.backward(dk)
        self.v_proj.backward(dv)
        
        return np.zeros_like(dq) # Input x gradient not needed for decoder-only usually, but good practice

class MLP(Module):
    def __init__(self, d_model):
        self.fc1 = Linear(d_model, 4 * d_model)
        self.fc2 = Linear(4 * d_model, d_model)
        self.cache = None

    def forward(self, x):
        x = self.fc1.forward(x)
        x = self.gelu(x)
        self.cache = x
        x = self.fc2.forward(x)
        return x

    def gelu(self, x):
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

    def backward(self, dout):
        # Backprop fc2
        dout = self.fc2.backward(dout)
        
        # Backprop GELU
        x = self.cache
        tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3))
        dx = 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out**2) * np.sqrt(2/np.pi) * (1 + 3 * 0.044715 * x**2)
        dout = dout * dx
        
        # Backprop fc1
        self.fc1.backward(dout)
        return np.zeros_like(dout)

class TransformerBlock(Module):
    def __init__(self, d_model, n_head):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model)

    def forward(self, x):
        x = x + self.attn.forward(self.ln1.forward(x))
        x = x + self.mlp.forward(self.ln2.forward(x))
        return x

    def backward(self, dout):
        # Residual 2
        dout_mlp = self.mlp.backward(dout)
        dout_ln2 = self.ln2.backward(dout) # Gradient flows to ln2 input
        dout = dout + dout_mlp + dout_ln2 # Gradient flows to block input
        
        # Residual 1
        dout_attn = self.attn.backward(dout)
        dout_ln1 = self.ln1.backward(dout)
        dout = dout + dout_attn + dout_ln1
        
        return dout