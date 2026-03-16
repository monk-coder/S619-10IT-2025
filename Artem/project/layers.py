import numpy as np

class Module:
    def __init__(self):
        self.params = {}
        self.grads = {}
        self.cache = {}

    def zero_grad(self):
        for k in self.grads:
            self.grads[k] = np.zeros_like(self.grads[k])

    def get_params(self):
        return self.params

    def get_grads(self):
        return self.grads

class Linear(Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        scale = np.sqrt(2.0 / (in_features + out_features))
        self.params['W'] = np.random.randn(in_features, out_features) * scale
        self.params['b'] = np.zeros((1, out_features))
        self.grads['W'] = np.zeros_like(self.params['W'])
        self.grads['b'] = np.zeros_like(self.params['b'])

    def forward(self, x):
        self.cache['x'] = x
        return np.dot(x, self.params['W']) + self.params['b']

    def backward(self, dout):
        x = self.cache['x']
        
        # Handle both 2D (B, D) and 3D (B, T, D) inputs
        if x.ndim == 3:
            B, T, D = x.shape
            x_flat = x.reshape(-1, D)          # (B*T, D)
            dout_flat = dout.reshape(-1, dout.shape[-1])  # (B*T, V)
            
            self.grads['W'] = np.dot(x_flat.T, dout_flat)  # (D, V)
            self.grads['b'] = np.sum(dout, axis=(0, 1), keepdims=True)  # (1, V)
            
            dx = np.dot(dout, self.params['W'].T)  # (B, T, D)
        else:
            self.grads['W'] = np.dot(x.T, dout)
            self.grads['b'] = np.sum(dout, axis=0, keepdims=True)
            dx = np.dot(dout, self.params['W'].T)
            
        return dx

class Embedding(Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        scale = np.sqrt(1.0 / d_model)
        self.params['E'] = np.random.randn(vocab_size, d_model) * scale
        self.grads['E'] = np.zeros_like(self.params['E'])

    def forward(self, x):
        self.cache['x'] = x
        return self.params['E'][x]

    def backward(self, dout):
        x = self.cache['x']
        # x is (B, T), dout is (B, T, D)
        B, T, D = dout.shape
        
        # Flatten both
        x_flat = x.reshape(-1).astype(np.int64)  # (B*T,)
        dout_flat = dout.reshape(-1, D)  # (B*T, D)
        
        # Accumulate gradients using explicit loop (more reliable)
        for i in range(len(x_flat)):
            self.grads['E'][x_flat[i]] += dout_flat[i]
        
        return None

class LayerNorm(Module):
    def __init__(self, d_model, eps=1e-5):
        super().__init__()
        self.eps = eps
        self.params['gamma'] = np.ones((1, 1, d_model))
        self.params['beta'] = np.zeros((1, 1, d_model))
        self.grads['gamma'] = np.zeros_like(self.params['gamma'])
        self.grads['beta'] = np.zeros_like(self.params['beta'])

    def forward(self, x):
        self.cache['x'] = x
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        self.cache['mean'] = mean
        self.cache['var'] = var
        self.cache['x_norm'] = x_norm
        return self.params['gamma'] * x_norm + self.params['beta']

    def backward(self, dout):
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']
        
        N = x.shape[-1]
        
        self.grads['gamma'] = np.sum(dout * x_norm, axis=(0, 1), keepdims=True)
        self.grads['beta'] = np.sum(dout, axis=(0, 1), keepdims=True)
        
        dx_norm = dout * self.params['gamma']
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps)**(-1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True) + \
                dvar * np.sum(-2 * (x - mean), axis=-1, keepdims=True) / N
        
        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / N + dmean / N
        return dx

class MultiHeadAttention(Module):
    def __init__(self, d_model, n_head, causal=True):
        super().__init__()
        assert d_model % n_head == 0
        self.n_head = n_head
        self.d_head = d_model // n_head
        self.causal = causal
        
        self.Wq = Linear(d_model, d_model)
        self.Wk = Linear(d_model, d_model)
        self.Wv = Linear(d_model, d_model)
        self.Wo = Linear(d_model, d_model)
        
        for name, mod in [('Wq', self.Wq), ('Wk', self.Wk), ('Wv', self.Wv), ('Wo', self.Wo)]:
            for k, v in mod.params.items():
                self.params[f'{name}.{k}'] = v
            for k, v in mod.grads.items():
                self.grads[f'{name}.{k}'] = v

    def forward(self, x):
        B, T, C = x.shape
        
        q = self.Wq.forward(x)
        k = self.Wk.forward(x)
        v = self.Wv.forward(x)
        
        q = q.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        k = k.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        v = v.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        att = np.matmul(q, k.transpose(0, 1, 3, 2)) / np.sqrt(self.d_head)
        
        if self.causal:
            mask = np.tril(np.ones((T, T))).reshape(1, 1, T, T)
            att = np.where(mask == 0, -1e9, att)
        
        att_max = np.max(att, axis=-1, keepdims=True)
        att_exp = np.exp(att - att_max)
        att_sum = np.sum(att_exp, axis=-1, keepdims=True)
        att_prob = att_exp / (att_sum + 1e-9)
        
        self.cache['q'] = q
        self.cache['k'] = k
        self.cache['v'] = v
        self.cache['att_prob'] = att_prob
        
        out = np.matmul(att_prob, v)
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)
        return self.Wo.forward(out)

    def backward(self, dout):
        B, T, C = dout.shape
        
        # Backprop through Wo (returns gradient wrt attention output)
        dout = self.Wo.backward(dout)
        
        # Reshape to (B, n_head, T, d_head) to match attention shape
        dout = dout.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        
        att_prob = self.cache['att_prob']
        v = self.cache['v']
        q = self.cache['q']
        k = self.cache['k']
        
        # dv = att_prob^T @ dout
        dv = np.matmul(att_prob.transpose(0, 1, 3, 2), dout)
        
        # d_att_prob = dout @ v^T
        d_att_prob = np.matmul(dout, v.transpose(0, 1, 3, 2))
        
        # Softmax backward
        sum_term = np.sum(d_att_prob * att_prob, axis=-1, keepdims=True)
        d_att = att_prob * (d_att_prob - sum_term)
        d_att = d_att / np.sqrt(self.d_head)
        
        # dq = d_att @ k
        dq = np.matmul(d_att, k)
        # dk = d_att^T @ q
        dk = np.matmul(d_att.transpose(0, 1, 3, 2), q)
        
        # Transpose back to (B, T, n_head, d_head) and reshape to (B, T, C)
        dq = dq.transpose(0, 2, 1, 3).reshape(B, T, C)
        dk = dk.transpose(0, 2, 1, 3).reshape(B, T, C)
        dv = dv.transpose(0, 2, 1, 3).reshape(B, T, C)
        
        # Backprop through projections (these update internal grads)
        self.Wq.backward(dq)
        self.Wk.backward(dk)
        self.Wv.backward(dv)
        
        # IMPORTANT: Return sum of gradients from Q, K, V paths
        # Because x was used to compute q, k, v, the gradient flows back through all three
        return dq + dk + dv

class MLP(Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)
        
        for name, mod in [('fc1', self.fc1), ('fc2', self.fc2)]:
            for k, v in mod.params.items():
                self.params[f'{name}.{k}'] = v
            for k, v in mod.grads.items():
                self.grads[f'{name}.{k}'] = v

    def forward(self, x):
        x = self.fc1.forward(x)
        x_act = np.maximum(0, x)  # ReLU
        self.cache['x_act'] = x_act
        return self.fc2.forward(x_act)

    def backward(self, dout):
        dout = self.fc2.backward(dout)
        dout = dout * (self.cache['x_act'] > 0)
        return self.fc1.backward(dout)

class TransformerBlock(Module):
    def __init__(self, d_model, n_head, d_ff):
        super().__init__()
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        
        mods = [self.ln1, self.attn, self.ln2, self.mlp]
        for mod in mods:
            self.params.update(mod.params)
            self.grads.update(mod.grads)

    def forward(self, x):
        x = x + self.attn.forward(self.ln1.forward(x))
        x = x + self.mlp.forward(self.ln2.forward(x))
        return x

    def backward(self, dout):
        dout_mlp = dout
        dout = self.mlp.backward(dout)
        dout = self.ln2.backward(dout)
        dout += dout_mlp
        
        dout_attn = dout
        dout = self.attn.backward(dout)
        dout = self.ln1.backward(dout)
        dout += dout_attn
        
        return dout