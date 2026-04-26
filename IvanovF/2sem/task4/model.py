import numpy as np


def gelu(x):
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)))


def gelu_grad(x):
    tanh_arg = np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)
    tanh_val = np.tanh(tanh_arg)
    dtanh = 1.0 - tanh_val ** 2
    darg = np.sqrt(2.0 / np.pi) * (1.0 + 3 * 0.044715 * x ** 2)
    return 0.5 * (1.0 + tanh_val) + 0.5 * x * dtanh * darg


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


class LayerNorm:
    def __init__(self, d, eps=1e-5):
        self.d = d
        self.eps = eps
        self.gamma = np.ones(d, dtype=np.float32)
        self.beta = np.zeros(d, dtype=np.float32)
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta = np.zeros_like(self.beta)

    def forward(self, x):
        self._x = x
        self._mean = x.mean(axis=-1, keepdims=True)
        self._var = x.var(axis=-1, keepdims=True)
        self._xhat = (x - self._mean) / np.sqrt(self._var + self.eps)
        return self.gamma * self._xhat + self.beta

    def backward(self, dout):
        N = self.d
        xhat = self._xhat
        var = self._var

        self.dgamma += (dout * xhat).sum(axis=(0, 1)) if dout.ndim == 3 else (dout * xhat).reshape(-1, N).sum(0)
        self.dbeta += dout.sum(axis=(0, 1)) if dout.ndim == 3 else dout.reshape(-1, N).sum(0)

        dxhat = dout * self.gamma
        inv_std = 1.0 / np.sqrt(var + self.eps)

        dx = (1.0 / N) * inv_std * (
            N * dxhat
            - dxhat.sum(axis=-1, keepdims=True)
            - xhat * (dxhat * xhat).sum(axis=-1, keepdims=True)
        )
        return dx

    def params(self):
        return [("gamma", self.gamma, self.dgamma), ("beta", self.beta, self.dbeta)]

    def zero_grad(self):
        self.dgamma[:] = 0
        self.dbeta[:] = 0


class Linear:
    def __init__(self, in_d, out_d, bias=True):
        self.W = (np.random.randn(in_d, out_d) * np.sqrt(2.0 / in_d)).astype(np.float32)
        self.b = np.zeros(out_d, dtype=np.float32) if bias else None
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b) if bias else None

    def forward(self, x):
        self._x = x
        out = x @ self.W
        if self.b is not None:
            out = out + self.b
        return out

    def backward(self, dout):
        x = self._x
        shape = x.shape
        x2d = x.reshape(-1, shape[-1])
        dout2d = dout.reshape(-1, dout.shape[-1])

        self.dW += x2d.T @ dout2d
        if self.b is not None:
            self.db += dout2d.sum(0)

        dx = dout @ self.W.T
        return dx

    def params(self):
        p = [("W", self.W, self.dW)]
        if self.b is not None:
            p.append(("b", self.b, self.db))
        return p

    def zero_grad(self):
        self.dW[:] = 0
        if self.db is not None:
            self.db[:] = 0


class CausalSelfAttention:
    def __init__(self, d_model, n_head, T):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_model // n_head
        self.T = T

        self.qkv_proj = Linear(d_model, 3 * d_model)
        self.out_proj = Linear(d_model, d_model)

        mask = np.tril(np.ones((T, T), dtype=np.float32))
        self._mask = mask

    def forward(self, x):
        B, T, C = x.shape
        H = self.n_head
        D = self.d_head

        qkv = self.qkv_proj.forward(x)
        q, k, v = np.split(qkv, 3, axis=-1)

        def split_heads(t):
            return t.reshape(B, T, H, D).transpose(0, 2, 1, 3)

        q = split_heads(q)
        k = split_heads(k)
        v = split_heads(v)

        scale = 1.0 / np.sqrt(D)
        att = (q @ k.transpose(0, 1, 3, 2)) * scale

        mask = self._mask[:T, :T]
        att = np.where(mask == 0, -1e9, att)

        att = softmax(att, axis=-1)
        self._att = att
        self._v = v
        self._q = q
        self._k = k
        self._scale = scale
        self._BT = (B, T)

        out = att @ v
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)

        out = self.out_proj.forward(out)
        return out

    def backward(self, dout):
        B, T = self._BT
        H = self.n_head
        D = self.d_head
        C = self.d_model

        dout = self.out_proj.backward(dout)

        dout = dout.reshape(B, T, H, D).transpose(0, 2, 1, 3)

        dv = self._att.transpose(0, 1, 3, 2) @ dout
        datt = dout @ self._v.transpose(0, 1, 3, 2)

        att = self._att
        datt_pre = att * (datt - (datt * att).sum(axis=-1, keepdims=True))

        mask = self._mask[:T, :T]
        datt_pre = np.where(mask == 0, 0.0, datt_pre) * self._scale

        dq = datt_pre @ self._k
        dk = datt_pre.transpose(0, 1, 3, 2) @ self._q

        def merge_heads(t):
            return t.transpose(0, 2, 1, 3).reshape(B, T, C)

        dq = merge_heads(dq)
        dk = merge_heads(dk)
        dv = merge_heads(dv)

        dqkv = np.concatenate([dq, dk, dv], axis=-1)
        dx = self.qkv_proj.backward(dqkv)
        return dx

    def params(self):
        return self.qkv_proj.params() + self.out_proj.params()

    def zero_grad(self):
        self.qkv_proj.zero_grad()
        self.out_proj.zero_grad()


class MLP:
    def __init__(self, d_model):
        self.fc1 = Linear(d_model, 4 * d_model)
        self.fc2 = Linear(4 * d_model, d_model)

    def forward(self, x):
        self._x_in = x
        h = self.fc1.forward(x)
        self._h_pre = h
        h = gelu(h)
        self._h_act = h
        out = self.fc2.forward(h)
        return out

    def backward(self, dout):
        dh = self.fc2.backward(dout)
        dh = dh * gelu_grad(self._h_pre)
        dx = self.fc1.backward(dh)
        return dx

    def params(self):
        return self.fc1.params() + self.fc2.params()

    def zero_grad(self):
        self.fc1.zero_grad()
        self.fc2.zero_grad()


class TransformerBlock:
    def __init__(self, d_model, n_head, T):
        self.ln1 = LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head, T)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model)

    def forward(self, x):
        self._x = x
        h = self.ln1.forward(x)
        h = self.attn.forward(h)
        x = x + h
        self._x2 = x
        h2 = self.ln2.forward(x)
        h2 = self.mlp.forward(h2)
        out = x + h2
        return out

    def backward(self, dout):
        dh2 = self.mlp.backward(dout)
        dh2 = self.ln2.backward(dh2)
        dx2 = dout + dh2

        dh = self.attn.backward(dx2)
        dh = self.ln1.backward(dh)
        dx = dx2 + dh
        return dx

    def params(self):
        return self.ln1.params() + self.attn.params() + self.ln2.params() + self.mlp.params()

    def zero_grad(self):
        self.ln1.zero_grad()
        self.attn.zero_grad()
        self.ln2.zero_grad()
        self.mlp.zero_grad()


class TransformerLM:
    def __init__(self, vocab_size, d_model, n_head, n_layer, T):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_head = n_head
        self.n_layer = n_layer
        self.T = T

        scale = 0.02
        self.tok_emb = (np.random.randn(vocab_size, d_model) * scale).astype(np.float32)
        self.pos_emb = (np.random.randn(T, d_model) * scale).astype(np.float32)
        self.dtok_emb = np.zeros_like(self.tok_emb)
        self.dpos_emb = np.zeros_like(self.pos_emb)

        self.blocks = [TransformerBlock(d_model, n_head, T) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size, bias=False)

        self._x_ids = None

    def forward(self, x_ids):
        B, T = x_ids.shape
        self._x_ids = x_ids

        tok = self.tok_emb[x_ids]
        pos = self.pos_emb[:T]
        h = tok + pos
        self._h0 = h

        for block in self.blocks:
            h = block.forward(h)

        h = self.ln_f.forward(h)
        logits = self.head.forward(h)
        return logits

    def backward(self, dlogits):
        B, T = self._x_ids.shape

        dh = self.head.backward(dlogits)
        dh = self.ln_f.backward(dh)

        for block in reversed(self.blocks):
            dh = block.backward(dh)

        np.add.at(self.dtok_emb, self._x_ids, dh)
        self.dpos_emb[:T] += dh.sum(axis=0)

    def params(self):
        p = [
            ("tok_emb", self.tok_emb, self.dtok_emb),
            ("pos_emb", self.pos_emb, self.dpos_emb),
        ]
        for i, block in enumerate(self.blocks):
            p += block.params()
        p += self.ln_f.params()
        p += self.head.params()
        return p

    def zero_grad(self):
        self.dtok_emb[:] = 0
        self.dpos_emb[:] = 0
        for block in self.blocks:
            block.zero_grad()
        self.ln_f.zero_grad()
        self.head.zero_grad()

    def save(self, path):
        arrays = {}
        seen = {}
        for name, w, _ in self.params():
            cnt = seen.get(name, 0)
            key = name if cnt == 0 else f"{name}_{cnt}"
            seen[name] = cnt + 1
            arrays[key] = w
        arrays["config"] = np.array([self.vocab_size, self.d_model, self.n_head, self.n_layer, self.T])
        np.savez(path, **arrays)

    @classmethod
    def load(cls, path):
        data = np.load(path + ".npz", allow_pickle=True)
        cfg = data["config"]
        vocab_size, d_model, n_head, n_layer, T = int(cfg[0]), int(cfg[1]), int(cfg[2]), int(cfg[3]), int(cfg[4])

        model = cls(vocab_size, d_model, n_head, n_layer, T)
        seen = {}
        for name, w, _ in model.params():
            cnt = seen.get(name, 0)
            key = name if cnt == 0 else f"{name}_{cnt}"
            seen[name] = cnt + 1
            if key in data:
                w[:] = data[key]
        return model


def loss_fn(logits, targets):
    B, T, V = logits.shape
    logits2d = logits.reshape(B * T, V)
    targets1d = targets.reshape(B * T)

    logits2d = logits2d - logits2d.max(axis=1, keepdims=True)
    exp_l = np.exp(logits2d)
    probs = exp_l / exp_l.sum(axis=1, keepdims=True)

    N = B * T
    log_probs = np.log(probs[np.arange(N), targets1d] + 1e-9)
    loss = -log_probs.mean()

    dlogits2d = probs.copy()
    dlogits2d[np.arange(N), targets1d] -= 1.0
    dlogits2d /= N

    dlogits = dlogits2d.reshape(B, T, V)
    return loss, dlogits


class AdamOptimizer:
    def __init__(self, params, lr=3e-4, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.0):
        self.params = params
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        self.t = 0
        self.m = [np.zeros_like(w) for _, w, _ in params]
        self.v = [np.zeros_like(w) for _, w, _ in params]

    def step(self):
        self.t += 1
        b1, b2 = self.beta1, self.beta2
        for i, (name, w, dw) in enumerate(self.params):
            g = dw
            if self.weight_decay > 0 and w.ndim >= 2:
                g = g + self.weight_decay * w
            self.m[i] = b1 * self.m[i] + (1 - b1) * g
            self.v[i] = b2 * self.v[i] + (1 - b2) * g * g
            m_hat = self.m[i] / (1 - b1 ** self.t)
            v_hat = self.v[i] / (1 - b2 ** self.t)
            w -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)