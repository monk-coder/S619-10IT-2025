import numpy as np


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.cache = {}

    def forward(self, x):
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        out = self.gamma * x_norm + self.beta

        self.cache = {'x': x, 'mean': mean, 'var': var, 'x_norm': x_norm}
        return out

    def backward(self, dout):
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']

        dgamma = np.sum(dout * x_norm, axis=(0, 1))
        dbeta = np.sum(dout, axis=(0, 1))

        dx_norm = dout * self.gamma
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps) ** (-1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True) + dvar * np.mean(-2 * (x - mean),
                                                                                                        axis=-1,
                                                                                                        keepdims=True)
        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / x.shape[-1] + dmean / x.shape[-1]

        return dx, dgamma, dbeta


class Linear:
    def __init__(self, in_features, out_features):
        self.W = np.random.randn(in_features, out_features) * 0.02
        self.b = np.zeros(out_features)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        return x @ self.W + self.b

    def backward(self, dout):
        x = self.cache['x']
        dW = x.reshape(-1, x.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        db = np.sum(dout, axis=(0, 1))
        dx = dout @ self.W.T
        return dx, dW, db


class GELU:
    def __init__(self):
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def backward(self, dout):
        x = self.cache['x']
        tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3))
        sech2 = 1 - tanh_out ** 2
        grad = 0.5 * (1 + tanh_out) + 0.5 * x * sech2 * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x ** 2)
        return dout * grad


class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head

        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)
        self.W_o = Linear(d_model, d_model)

        self.cache = {}

    def forward(self, x, mask=None):
        batch_size, seq_len, _ = x.shape

        # Линейные проекции
        Q = self.W_q.forward(x)
        K = self.W_k.forward(x)
        V = self.W_v.forward(x)

        # Разделение на головы
        Q = Q.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)

        # Attention scores
        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.head_dim)

        if mask is not None:
            scores = scores * mask + (1 - mask) * (-1e9)

        attn = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn = attn / np.sum(attn, axis=-1, keepdims=True)

        # Применение attention к значениям
        out = (attn @ V).transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        out = self.W_o.forward(out)

        self.cache = {'Q': Q, 'K': K, 'V': V, 'attn': attn, 'mask': mask, 'batch_size': batch_size, 'seq_len': seq_len}
        return out

    def backward(self, dout):
        batch_size = self.cache['batch_size']
        seq_len = self.cache['seq_len']

        dout = self.W_o.backward(dout.reshape(-1, self.d_model))[0].reshape(batch_size, seq_len, self.d_model)
        dout = dout.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)

        Q = self.cache['Q']
        K = self.cache['K']
        V = self.cache['V']
        attn = self.cache['attn']

        dV = attn.transpose(0, 1, 3, 2) @ dout
        dattn = dout @ V.transpose(0, 1, 3, 2)

        dscores = dattn * attn * (1 - attn)
        dscores = dscores / np.sqrt(self.head_dim)

        dQ = dscores @ K
        dK = dscores.transpose(0, 1, 3, 2) @ Q

        dQ = dQ.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dK = dK.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dV = dV.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)

        dQ, dW_q, db_q = self.W_q.backward(dQ.reshape(-1, self.d_model))
        dK, dW_k, db_k = self.W_k.backward(dK.reshape(-1, self.d_model))
        dV, dW_v, db_v = self.W_v.backward(dV.reshape(-1, self.d_model))

        return dQ + dK + dV, (dW_q, dW_k, dW_v), (db_q, db_k, db_v)


class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.act = GELU()
        self.fc2 = Linear(d_ff, d_model)

    def forward(self, x):
        x = self.fc1.forward(x)
        x = self.act.forward(x)
        x = self.fc2.forward(x)
        return x

    def backward(self, dout):
        dout = self.fc2.backward(dout)[0]
        dout = self.act.backward(dout)
        dout = self.fc1.backward(dout)[0]
        return dout


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)

    def forward(self, x, mask):
        # Attention с residual connection
        attn_out = self.attn.forward(self.ln1.forward(x), mask)
        x = x + attn_out

        # MLP с residual connection
        mlp_out = self.mlp.forward(self.ln2.forward(x))
        x = x + mlp_out
        return x

    def backward(self, dout):
        # Backward для MLP части
        dout_mlp = self.mlp.backward(dout)
        dout_ln2, dgamma2, dbeta2 = self.ln2.backward(dout_mlp)

        # Backward для Attention части с residual
        dout_attn = dout
        dout_ln1, dgamma1, dbeta1 = self.ln1.backward(dout_attn)
        dout_attn, dW_attn, db_attn = self.attn.backward(dout_ln1)

        return dout_attn + dout_ln2, (dgamma1, dbeta1, dgamma2, dbeta2), dW_attn, db_attn


class TransformerLM:
    def __init__(self, vocab_size, d_model=256, n_head=4, n_layer=4, d_ff=512, max_seq_len=256):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.n_layer = n_layer

        # Эмбеддинги
        self.token_embedding = np.random.randn(vocab_size, d_model) * 0.02
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * 0.02

        # Блоки трансформера
        self.blocks = [TransformerBlock(d_model, n_head, d_ff) for _ in range(n_layer)]

        # Выходной слой
        self.ln_final = LayerNorm(d_model)
        self.fc_out = Linear(d_model, vocab_size)

        # Маска для причинности
        self.causal_mask = np.tril(np.ones((max_seq_len, max_seq_len))).reshape(1, 1, max_seq_len, max_seq_len)

    def forward(self, x):
        batch_size, seq_len = x.shape

        # Эмбеддинги
        x_emb = self.token_embedding[x]
        x_emb = x_emb + self.pos_embedding[:seq_len]

        # Применение блоков трансформера
        for block in self.blocks:
            x_emb = block.forward(x_emb, self.causal_mask[:, :, :seq_len, :seq_len])

        # Выходной слой
        x_norm = self.ln_final.forward(x_emb)
        logits = self.fc_out.forward(x_norm)

        return logits

    def parameters(self):
        params = []
        params.append(self.token_embedding)
        params.append(self.pos_embedding)
        for block in self.blocks:
            params.append(block.ln1.gamma)
            params.append(block.ln1.beta)
            params.append(block.attn.W_q.W)
            params.append(block.attn.W_q.b)
            params.append(block.attn.W_k.W)
            params.append(block.attn.W_k.b)
            params.append(block.attn.W_v.W)
            params.append(block.attn.W_v.b)
            params.append(block.attn.W_o.W)
            params.append(block.attn.W_o.b)
            params.append(block.ln2.gamma)
            params.append(block.ln2.beta)
            params.append(block.mlp.fc1.W)
            params.append(block.mlp.fc1.b)
            params.append(block.mlp.fc2.W)
            params.append(block.mlp.fc2.b)
        params.append(self.ln_final.gamma)
        params.append(self.ln_final.beta)
        params.append(self.fc_out.W)
        params.append(self.fc_out.b)
        return params

    def train(self):
        self.training = True

    def eval(self):
        self.training = False