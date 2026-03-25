import numpy as np


def softmax(x, axis=-1):
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class Linear:
    def __init__(self, in_feat, out_feat):
        self.W = np.random.randn(in_feat, out_feat) * 0.02
        self.b = np.zeros(out_feat)
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, x):
        self.x = x
        return x @ self.W + self.b

    def backward(self, dout):
        # dout shape: (B, T, out_feat)
        dout_flat = dout.reshape(-1, dout.shape[-1])
        x_flat = self.x.reshape(-1, self.x.shape[-1])
        self.dW = x_flat.T @ dout_flat
        self.db = np.sum(dout_flat, axis=0)
        return dout @ self.W.T


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta = np.zeros_like(self.beta)
        self.eps = eps

    def forward(self, x):
        self.x = x
        self.mu = np.mean(x, axis=-1, keepdims=True)
        self.var = np.var(x, axis=-1, keepdims=True)
        self.std = np.sqrt(self.var + self.eps)
        self.x_hat = (x - self.mu) / self.std
        return self.gamma * self.x_hat + self.beta

    def backward(self, dout):
        D = self.x.shape[-1]
        self.dgamma = np.sum(dout * self.x_hat, axis=tuple(range(dout.ndim - 1)))
        self.dbeta = np.sum(dout, axis=tuple(range(dout.ndim - 1)))

        dx_hat = dout * self.gamma
        dvar = np.sum(dx_hat * (self.x - self.mu) * -0.5 * (self.var + self.eps) ** (-1.5), axis=-1, keepdims=True)
        dmu = np.sum(dx_hat * -1.0 / self.std, axis=-1, keepdims=True) + dvar * np.sum(-2.0 * (self.x - self.mu),
                                                                                       axis=-1, keepdims=True) / D
        return dx_hat / self.std + dvar * 2.0 * (self.x - self.mu) / D + dmu / D


class Embedding:
    def __init__(self, vocab_size, d_model):
        self.weight = np.random.randn(vocab_size, d_model) * 0.02
        self.dweight = np.zeros_like(self.weight)

    def forward(self, idx):
        self.idx = idx
        return self.weight[idx]

    def backward(self, dout):
        self.dweight.fill(0)
        # Используем ravel() и reshape, чтобы корректно сопоставить индексы и градиенты
        np.add.at(self.dweight, self.idx.ravel(), dout.reshape(-1, dout.shape[-1]))


class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        self.n_head = n_head
        self.d_k = d_model // n_head
        self.q_lin = Linear(d_model, d_model)
        self.k_lin = Linear(d_model, d_model)
        self.v_lin = Linear(d_model, d_model)
        self.out_lin = Linear(d_model, d_model)

    def forward(self, x, mask=None):
        B, T, C = x.shape
        self.q = self.q_lin.forward(x).reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        self.k = self.k_lin.forward(x).reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        self.v = self.v_lin.forward(x).reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)

        scores = (self.q @ self.k.transpose(0, 1, 3, 2)) / np.sqrt(self.d_k)
        if mask is not None:
            scores += (mask * -1e9)

        self.attn = softmax(scores, axis=-1)
        out = self.attn @ self.v
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)
        return self.out_lin.forward(out)

    def backward(self, dout):
        B, T, C = dout.shape
        dout_out_lin = self.out_lin.backward(dout)
        dout_out_lin = dout_out_lin.reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)

        # Gradient of attention product (attn @ v)
        dv = self.attn.transpose(0, 1, 3, 2) @ dout_out_lin
        dattn_raw = dout_out_lin @ self.v.transpose(0, 1, 3, 2)

        # Gradient of Softmax
        dscores = self.attn * (dattn_raw - np.sum(self.attn * dattn_raw, axis=-1, keepdims=True))
        dscores /= np.sqrt(self.d_k)

        dq = dscores @ self.k
        dk = dscores.transpose(0, 1, 3, 2) @ self.q

        # Сборка градиентов для линейных слоев
        dq = dq.transpose(0, 2, 1, 3).reshape(B, T, C)
        dk = dk.transpose(0, 2, 1, 3).reshape(B, T, C)
        dv = dv.transpose(0, 2, 1, 3).reshape(B, T, C)

        return self.q_lin.backward(dq) + self.k_lin.backward(dk) + self.v_lin.backward(dv)


class FFN:
    def __init__(self, d_model, d_ff):
        self.l1 = Linear(d_model, d_ff)
        self.l2 = Linear(d_ff, d_model)

    def forward(self, x):
        self.x1 = self.l1.forward(x)
        self.act = np.maximum(0, self.x1)  # ReLU
        return self.l2.forward(self.act)

    def backward(self, dout):
        dact = self.l2.backward(dout)
        dx1 = dact * (self.x1 > 0)
        return self.l1.backward(dx1)


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.mha = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.ffn = FFN(d_model, d_ff)

    def forward(self, x, mask):
        self.x_ln1 = self.ln1.forward(x)
        self.attn_out = self.mha.forward(self.x_ln1, mask)
        self.res1 = x + self.attn_out

        self.x_ln2 = self.ln2.forward(self.res1)
        self.ffn_out = self.ffn.forward(self.x_ln2)
        return self.res1 + self.ffn_out

    def backward(self, dout):
        # Вторая остаточная связь (residual connection)
        df_ffn = self.ffn.backward(dout)
        dx_ln2 = self.ln2.backward(df_ffn)
        dout_res1 = dout + dx_ln2

        # Первая остаточная связь
        df_mha = self.mha.backward(dout_res1)
        dx_ln1 = self.ln1.backward(df_mha)
        return dout_res1 + dx_ln1


class GPT:
    def __init__(self, vocab_size, d_model, n_head, n_layer, d_ff, seq_len):
        self.tok_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(seq_len, d_model)
        self.blocks = [TransformerBlock(d_model, n_head, d_ff) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size)
        self.seq_len = seq_len

    def forward(self, idx):
        B, T = idx.shape
        pos = np.arange(T)[None, :]
        x = self.tok_emb.forward(idx) + self.pos_emb.forward(pos)

        mask = np.triu(np.ones((T, T)), k=1)
        for block in self.blocks:
            x = block.forward(x, mask)

        x = self.ln_f.forward(x)
        return self.head.forward(x)

    def backward(self, dlogits):
        dout = self.head.backward(dlogits)
        dout = self.ln_f.backward(dout)
        for block in reversed(self.blocks):
            dout = block.backward(dout)

        # Ключевой момент: токены специфичны для каждого примера в батче
        self.tok_emb.backward(dout)

        # А позиции — общие для всего батча, поэтому суммируем градиент
        dpos = np.sum(dout, axis=0, keepdims=True)
        self.pos_emb.backward(dpos)

    def get_params(self):
        params, grads = [], []
        # Собираем всё для оптимизатора
        layers = [self.tok_emb, self.pos_emb, self.ln_f, self.head]
        for b in self.blocks:
            layers += [b.ln1, b.mha.q_lin, b.mha.k_lin, b.mha.v_lin, b.mha.out_lin, b.ln2, b.ffn.l1, b.ffn.l2]

        for layer in layers:
            if isinstance(layer, Embedding):
                params.append(layer.weight);
                grads.append(layer.dweight)
            elif isinstance(layer, Linear):
                params.append(layer.W);
                grads.append(layer.dW)
                params.append(layer.b);
                grads.append(layer.db)
            elif isinstance(layer, LayerNorm):
                params.append(layer.gamma);
                grads.append(layer.dgamma)
                params.append(layer.beta);
                grads.append(layer.dbeta)
        return params, grads


class Adam:
    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.params = params
        self.lr, self.beta1, self.beta2, self.eps = lr, beta1, beta2, eps
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0

    def step(self, grads):
        self.t += 1
        for i in range(len(self.params)):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grads[i]
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grads[i] ** 2)
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)
            self.params[i] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)