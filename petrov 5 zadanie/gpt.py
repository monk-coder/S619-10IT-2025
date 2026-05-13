import numpy as np
import config

def gelu(x):
    return 0.5 * x * (1 + np.tanh(config.SQRT_2_PI * (x + config.GELU_COEF * x**3)))

def gelu_backward(x):
    tanh_out = np.tanh(config.SQRT_2_PI * (x + config.GELU_COEF * x**3))
    return 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out**2) * config.SQRT_2_PI * (1 + 3 * config.GELU_COEF * x**2)

class Embedding:
    def __init__(self, num_embeddings, embedding_dim):
        self.weight = np.random.randn(num_embeddings, embedding_dim) * 0.02
        self.grad = np.zeros_like(self.weight)
    def forward(self, x):
        self.x = x
        return self.weight[x]
    def backward(self, dout):
        self.grad.fill(0)
        np.add.at(self.grad, self.x, dout)
    def update(self, lr):
        self.weight -= lr * self.grad

class Linear:
    def __init__(self, in_features, out_features, bias=True):
        self.weight = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        self.bias = np.zeros(out_features) if bias else None
        self.grad_weight = np.zeros_like(self.weight)
        self.grad_bias = np.zeros(out_features) if bias else None
    def forward(self, x):
        self.x = x
        out = x @ self.weight
        if self.bias is not None: out = out + self.bias
        return out
    def backward(self, dout):
        self.grad_weight = self.x.reshape(-1, self.x.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        if self.bias is not None: self.grad_bias = dout.sum(axis=tuple(range(dout.ndim-1)))
        return dout @ self.weight.T
    def update(self, lr):
        self.weight -= lr * self.grad_weight
        if self.bias is not None: self.bias -= lr * self.grad_bias

class LayerNorm:
    def __init__(self, d_model, eps=None):
        self.eps = eps if eps is not None else config.LAYER_NORM_EPS
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.grad_gamma = np.zeros(d_model)
        self.grad_beta = np.zeros(d_model)
    def forward(self, x):
        self.x_shape = x.shape
        x = x.reshape(-1, x.shape[-1])
        self.mean = x.mean(axis=0)
        self.var = x.var(axis=0) + self.eps
        x_norm = (x - self.mean) / np.sqrt(self.var)
        self.x_norm = x_norm
        out = x_norm * self.gamma + self.beta
        return out.reshape(self.x_shape)
    def backward(self, dout):
        dout = dout.reshape(-1, dout.shape[-1])
        N = dout.shape[0]
        self.grad_gamma = (dout * self.x_norm).sum(axis=0)
        self.grad_beta = dout.sum(axis=0)
        dx_norm = dout * self.gamma
        dvar = (dx_norm * (self.x_norm - self.mean) * -0.5 * np.power(self.var, -1.5)).sum(axis=0)
        dmean = (-dx_norm / np.sqrt(self.var)).sum(axis=0) + dvar * (-2 * (self.x_norm - self.mean)).sum(axis=0) / N
        dx = dx_norm / np.sqrt(self.var) + dvar * 2 * (self.x_norm - self.mean) / N + dmean / N
        return dx.reshape(self.x_shape)
    def update(self, lr):
        self.gamma -= lr * self.grad_gamma
        self.beta -= lr * self.grad_beta

class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)
    def forward(self, x, training=True):
        self.x = x
        x = self.fc1.forward(x)
        self.x_act = gelu(x)
        return self.fc2.forward(self.x_act)
    def backward(self, dout):
        dout = self.fc2.backward(dout)
        dout = dout * gelu_backward(self.x_act)
        return self.fc1.backward(dout)
    def update(self, lr):
        self.fc1.update(lr)
        self.fc2.update(lr)

class MultiHeadAttention:
    def __init__(self, d_model, n_head, dropout=0.1):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_model // n_head
        self.wq = Linear(d_model, d_model)
        self.wk = Linear(d_model, d_model)
        self.wv = Linear(d_model, d_model)
        self.wo = Linear(d_model, d_model)
        self.dropout = dropout
    def _causal_mask(self, T):
        return np.triu(np.ones((T, T)) * config.MASK_VALUE, k=1)
    def forward(self, x, training=True):
        B, T, D = x.shape
        Q = self.wq.forward(x)
        K = self.wk.forward(x)
        V = self.wv.forward(x)
        def split_heads(x):
            return x.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        Q_h = split_heads(Q)
        K_h = split_heads(K)
        V_h = split_heads(V)
        scores = Q_h @ K_h.transpose(0, 1, 3, 2) / np.sqrt(self.d_head)
        mask = self._causal_mask(T)
        scores = scores + mask
        scores_max = np.max(scores, axis=-1, keepdims=True)
        attn = np.exp(scores - scores_max)
        attn = attn / (attn.sum(axis=-1, keepdims=True) + config.EPS_SOFTMAX)
        if training and self.dropout > 0:
            mask_drop = (np.random.rand(*attn.shape) > self.dropout).astype(float)
            attn = attn * mask_drop / (1 - self.dropout + config.EPS_SOFTMAX)
        self.attn = attn
        self.V_h = V_h
        self.Q_h = Q_h
        self.K_h = K_h
        out = (attn @ V_h).transpose(0, 2, 1, 3).reshape(B, T, D)
        return self.wo.forward(out)
    def backward(self, dout):
        B, T, D = dout.shape
        dout = self.wo.backward(dout)
        dout = dout.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        dV_h = self.attn.transpose(0, 1, 3, 2) @ dout
        d_scores = dout @ self.V_h.transpose(0, 1, 3, 2)
        attn = self.attn
        d_scores = attn * (d_scores - np.sum(attn * d_scores, axis=-1, keepdims=True))
        dQ_h = d_scores @ self.K_h / np.sqrt(self.d_head)
        dK_h = d_scores.transpose(0, 1, 3, 2) @ self.Q_h / np.sqrt(self.d_head)
        def merge_heads(x):
            return x.transpose(0, 2, 1, 3).reshape(B, T, D)
        dQ = merge_heads(dQ_h)
        dK = merge_heads(dK_h)
        dV = merge_heads(dV_h)
        return self.wq.backward(dQ) + self.wk.backward(dK) + self.wv.backward(dV)
    def update(self, lr):
        self.wq.update(lr)
        self.wk.update(lr)
        self.wv.update(lr)
        self.wo.update(lr)

class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff, dropout=0.1):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head, dropout)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.dropout = dropout
    def forward(self, x, training=True):
        x_norm = self.ln1.forward(x)
        x_attn = self.attn.forward(x_norm, training)
        if training and self.dropout > 0:
            x_attn = x_attn * (np.random.rand(*x_attn.shape) > self.dropout) / (1 - self.dropout + config.EPS_SOFTMAX)
        x = x + x_attn
        x_norm = self.ln2.forward(x)
        x_mlp = self.mlp.forward(x_norm, training)
        if training and self.dropout > 0:
            x_mlp = x_mlp * (np.random.rand(*x_mlp.shape) > self.dropout) / (1 - self.dropout + config.EPS_SOFTMAX)
        x = x + x_mlp
        return x
    def backward(self, dout):
        dout = self.mlp.backward(dout)
        dout = self.ln2.backward(dout)
        dout = self.attn.backward(dout)
        dout = self.ln1.backward(dout)
        return dout
    def update(self, lr):
        self.ln1.update(lr)
        self.attn.update(lr)
        self.ln2.update(lr)
        self.mlp.update(lr)

class TransformerLM:
    def __init__(self, vocab_size, d_model=64, n_head=2, n_layer=2, d_ff=128, max_seq_len=64, dropout=0.1):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_seq_len, d_model)
        self.blocks = [TransformerBlock(d_model, n_head, d_ff, dropout) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size, bias=False)
    def forward(self, x, training=True):
        B, T = x.shape
        tok_emb = self.token_emb.forward(x)
        pos = np.arange(T)[None, :]
        pos_emb = self.pos_emb.forward(pos)
        x = tok_emb + pos_emb
        for block in self.blocks:
            x = block.forward(x, training)
        x = self.ln_f.forward(x)
        return self.head.forward(x)
    def backward(self, dout):
        dout = self.head.backward(dout)
        dout = self.ln_f.backward(dout)
        for block in reversed(self.blocks):
            dout = block.backward(dout)
        self.pos_emb.backward(dout)
        self.token_emb.backward(dout)
    def update(self, lr):
        self.token_emb.update(lr)
        self.pos_emb.update(lr)
        for block in self.blocks:
            block.update(lr)
        self.ln_f.update(lr)
        self.head.update(lr)
    def get_params(self):
        params = {}
        def collect(obj, prefix):
            for attr in dir(obj):
                if not attr.startswith('_') and hasattr(getattr(obj, attr), 'shape'):
                    val = getattr(obj, attr)
                    if isinstance(val, np.ndarray):
                        params[f"{prefix}.{attr}"] = val.copy()
                elif hasattr(getattr(obj, attr), 'weight'):
                    collect(getattr(obj, attr), f"{prefix}.{attr}")
        collect(self, 'model')
        return params
    def load_params(self, params):
        def assign(obj, prefix):
            for attr in dir(obj):
                if not attr.startswith('_') and hasattr(getattr(obj, attr), 'shape'):
                    key = f"{prefix}.{attr}"
                    if key in params:
                        getattr(obj, attr)[:] = params[key]
                elif hasattr(getattr(obj, attr), 'weight'):
                    assign(getattr(obj, attr), f"{prefix}.{attr}")
        assign(self, 'model')

def cross_entropy_loss(logits, targets):
    B, T, V = logits.shape
    logits_max = np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits - logits_max)
    probs = exp_logits / (exp_logits.sum(axis=-1, keepdims=True) + config.EPS_SOFTMAX)
    targets_flat = targets.reshape(-1)
    probs_flat = probs.reshape(-1, V)
    one_hot = np.zeros_like(probs_flat)
    one_hot[np.arange(len(targets_flat)), targets_flat] = 1
    loss = -np.sum(one_hot * np.log(probs_flat + config.EPS_LOG)) / (B * T)
    dout = (probs - one_hot).reshape(B, T, V) / (B * T)
    return loss, dout

def compute_accuracy(logits, targets):
    preds = np.argmax(logits, axis=-1)
    correct = (preds == targets).sum()
    total = targets.size
    return correct / total if total > 0 else 0.0

class Adam:
    def __init__(self, model, lr=1e-3, beta1=0.9, beta2=0.999, eps=None):
        self.model = model
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps if eps is not None else config.EPS
        self.t = 0
        self.m = {}
        self.v = {}
        for name, param, grad in self._get_params(model):
            self.m[name] = np.zeros_like(param)
            self.v[name] = np.zeros_like(param)
    def _get_params(self, obj, prefix='model'):
        for attr in dir(obj):
            if attr.startswith('_'): continue
            val = getattr(obj, attr)
            if isinstance(val, np.ndarray) and hasattr(obj, 'grad') and hasattr(getattr(obj, 'grad', None), 'shape') and getattr(obj, 'grad').shape == val.shape:
                yield f"{prefix}.{attr}", val, getattr(obj, 'grad')
            elif hasattr(val, 'weight'):
                yield from self._get_params(val, f"{prefix}.{attr}")
    def step(self):
        self.t += 1
        lr_t = self.lr * np.sqrt(1 - self.beta2**self.t) / (1 - self.beta1**self.t)
        for name, param, grad in self._get_params(self.model):
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * grad**2
            param -= lr_t * self.m[name] / (np.sqrt(self.v[name]) + self.eps)
