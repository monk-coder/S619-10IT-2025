import numpy as np

class Layer:
    """Базовый класс для всех слоёв."""
    def __init__(self):
        self.params = {}
        self.grads = {}
        self.cache = {}  # для хранения промежуточных значений при forward

    def forward(self, x):
        raise NotImplementedError

    def backward(self, dout):
        raise NotImplementedError

class Embedding(Layer):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.params['W'] = np.random.randn(vocab_size, d_model) * 0.01
        self.grads['W'] = np.zeros_like(self.params['W'])

    def forward(self, x):
        self.cache['x'] = x
        out = self.params['W'][x]
        return out

    def backward(self, dout):
        x = self.cache['x']
        self.grads['W'] = np.zeros_like(self.params['W'])
        np.add.at(self.grads['W'], x, dout)
        return None

class PositionalEncoding(Layer):
    def __init__(self, max_len, d_model):
        super().__init__()
        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        self.params['pe'] = pe
        self.grads['pe'] = np.zeros_like(pe)

    def forward(self, x):
        seq_len = x.shape[1]
        self.cache['seq_len'] = seq_len
        return x + self.params['pe'][:seq_len, :]

    def backward(self, dout):
        return dout

class LayerNorm(Layer):
    def __init__(self, d_model, eps=1e-5):
        super().__init__()
        self.eps = eps
        self.params['gamma'] = np.ones(d_model)
        self.params['beta'] = np.zeros(d_model)
        self.grads['gamma'] = np.zeros(d_model)
        self.grads['beta'] = np.zeros(d_model)

    def forward(self, x):
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        out = self.params['gamma'] * x_norm + self.params['beta']
        self.cache['x'] = x
        self.cache['mean'] = mean
        self.cache['var'] = var
        self.cache['x_norm'] = x_norm
        return out

    def backward(self, dout):
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']
        gamma = self.params['gamma']
        eps = self.eps

        N, T, D = dout.shape
        dgamma = np.sum(dout * x_norm, axis=(0, 1))
        dbeta = np.sum(dout, axis=(0, 1))

        dx_norm = dout * gamma
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * np.power(var + eps, -1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + eps), axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)
        dx = dx_norm / np.sqrt(var + eps) + dvar * 2 * (x - mean) / D + dmean / D

        self.grads['gamma'] = dgamma
        self.grads['beta'] = dbeta
        return dx

class Linear(Layer):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.params['W'] = np.random.randn(in_features, out_features) * 0.01
        self.params['b'] = np.zeros(out_features)
        self.grads['W'] = np.zeros_like(self.params['W'])
        self.grads['b'] = np.zeros_like(self.params['b'])

    def forward(self, x):
        self.cache['x'] = x
        return x @ self.params['W'] + self.params['b']

    def backward(self, dout):
        x = self.cache['x']
        self.grads['W'] = x.reshape(-1, x.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        self.grads['b'] = np.sum(dout, axis=tuple(range(dout.ndim-1)))
        dx = dout @ self.params['W'].T
        return dx

class MultiHeadAttention(Layer):
    def __init__(self, d_model, n_head, causal=True):
        super().__init__()
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head
        assert d_model % n_head == 0, "d_model must be divisible by n_head"
        self.causal = causal

        self.Wq = Linear(d_model, d_model)
        self.Wk = Linear(d_model, d_model)
        self.Wv = Linear(d_model, d_model)
        self.Wo = Linear(d_model, d_model)

        self.sub_layers = [self.Wq, self.Wk, self.Wv, self.Wo]

    def forward(self, x):
        B, T, D = x.shape
        H = self.n_head
        hd = self.head_dim

        q = self.Wq.forward(x)
        k = self.Wk.forward(x)
        v = self.Wv.forward(x)

        q = q.reshape(B, T, H, hd).transpose(0, 2, 1, 3)
        k = k.reshape(B, T, H, hd).transpose(0, 2, 1, 3)
        v = v.reshape(B, T, H, hd).transpose(0, 2, 1, 3)

        scores = q @ k.transpose(0, 1, 3, 2) / np.sqrt(hd)

        if self.causal:
            mask = np.triu(np.ones((T, T), dtype=bool), k=1)
            scores = np.where(mask, -np.inf, scores)

        scores_max = np.max(scores, axis=-1, keepdims=True)
        scores_stable = scores - scores_max
        exp_scores = np.exp(scores_stable)
        attn_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

        self.cache['attn_weights'] = attn_weights
        self.cache['q'] = q
        self.cache['k'] = k
        self.cache['v'] = v
        self.cache['x_shape'] = (B, T, D)

        out = attn_weights @ v
        out = out.transpose(0, 2, 1, 3).reshape(B, T, D)
        out = self.Wo.forward(out)
        return out

    def backward(self, dout):
        B, T, D = self.cache['x_shape']
        H = self.n_head
        hd = self.head_dim

        dout = self.Wo.backward(dout)

        dout = dout.reshape(B, T, H, hd).transpose(0, 2, 1, 3)

        attn_weights = self.cache['attn_weights']
        q = self.cache['q']
        k = self.cache['k']
        v = self.cache['v']

        dv = attn_weights.transpose(0,1,3,2) @ dout
        dattn = dout @ v.transpose(0,1,3,2)

        dattn_times_attn = attn_weights * dattn
        dscores = attn_weights * (dattn - np.sum(dattn_times_attn, axis=-1, keepdims=True))

        if self.causal:
            mask = np.triu(np.ones((T, T), dtype=bool), k=1)
            dscores = np.where(mask, 0, dscores)

        dq = dscores @ k
        dk = dscores.transpose(0,1,3,2) @ q

        dq = dq / np.sqrt(hd)
        dk = dk / np.sqrt(hd)

        dq = dq.transpose(0, 2, 1, 3).reshape(B, T, D)
        dk = dk.transpose(0, 2, 1, 3).reshape(B, T, D)
        dv = dv.transpose(0, 2, 1, 3).reshape(B, T, D)

        dx_q = self.Wq.backward(dq)
        dx_k = self.Wk.backward(dk)
        dx_v = self.Wv.backward(dv)

        dx = dx_q + dx_k + dx_v
        return dx

    def parameters(self):
        params = {}
        grads = {}
        for name, layer in [('Wq', self.Wq), ('Wk', self.Wk), ('Wv', self.Wv), ('Wo', self.Wo)]:
            for pname in layer.params:
                params[f'{name}_{pname}'] = layer.params[pname]
                grads[f'{name}_{pname}'] = layer.grads[pname]
        return params, grads

class MLP(Layer):
    def __init__(self, d_model, d_ff, activation='gelu'):
        super().__init__()
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)
        self.activation = activation
        self.sub_layers = [self.fc1, self.fc2]

    def forward(self, x):
        out = self.fc1.forward(x)
        if self.activation == 'gelu':
            out = 0.5 * out * (1 + np.tanh(np.sqrt(2 / np.pi) * (out + 0.044715 * out**3)))
        elif self.activation == 'relu':
            out = np.maximum(0, out)
        self.cache['pre_act'] = out
        out = self.fc2.forward(out)
        return out

    def backward(self, dout):
        dout = self.fc2.backward(dout)
        out = self.cache['pre_act']
        if self.activation == 'gelu':
            tanh_arg = np.sqrt(2 / np.pi) * (out + 0.044715 * out**3)
            sech2 = 1 / np.cosh(tanh_arg)**2
            dgelu = 0.5 * (1 + np.tanh(tanh_arg)) + 0.5 * out * sech2 * np.sqrt(2 / np.pi) * (1 + 3*0.044715*out**2)
        elif self.activation == 'relu':
            dgelu = (out > 0).astype(float)
        dout = dout * dgelu
        dout = self.fc1.backward(dout)
        return dout

    def parameters(self):
        params = {}
        grads = {}
        for name, layer in [('fc1', self.fc1), ('fc2', self.fc2)]:
            for pname in layer.params:
                params[f'{name}_{pname}'] = layer.params[pname]
                grads[f'{name}_{pname}'] = layer.grads[pname]
        return params, grads

class TransformerBlock(Layer):
    def __init__(self, d_model, n_head, d_ff, causal=True, dropout=0.0):
        super().__init__()
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head, causal)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.dropout = dropout

    def forward(self, x):
        attn_out = self.attn.forward(self.ln1.forward(x))
        x = x + attn_out
        mlp_out = self.mlp.forward(self.ln2.forward(x))
        x = x + mlp_out
        return x

    def backward(self, dout):
        dmlp = dout
        dln2 = self.mlp.backward(dmlp)
        dresidual_mlp = self.ln2.backward(dln2)

        dattn_out = dout + dresidual_mlp

        dln1 = self.attn.backward(dattn_out)
        dresidual_attn = self.ln1.backward(dln1)
        dx = dresidual_attn
        return dx

    def parameters(self):
        params = {}
        grads = {}
        for name, layer in [('ln1', self.ln1), ('attn', self.attn), ('ln2', self.ln2), ('mlp', self.mlp)]:
            p, g = layer.parameters() if hasattr(layer, 'parameters') else (layer.params, layer.grads)
            for key in p:
                params[f'{name}_{key}'] = p[key]
                grads[f'{name}_{key}'] = g[key]
        return params, grads

class TransformerLM(Layer):
    def __init__(self, vocab_size, d_model, n_layer, n_head, max_len, causal=True):
        super().__init__()
        self.token_embedding = Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(max_len, d_model)
        self.blocks = []
        for _ in range(n_layer):
            self.blocks.append(TransformerBlock(d_model, n_head, d_model*4, causal))
        self.ln_final = LayerNorm(d_model)
        self.output = Linear(d_model, vocab_size)
        self.causal = causal

    def forward(self, x):
        out = self.token_embedding.forward(x)
        out = self.pos_encoding.forward(out)
        for block in self.blocks:
            out = block.forward(out)
        out = self.ln_final.forward(out)
        logits = self.output.forward(out)
        return logits

    def backward(self, dout):
        dout = self.output.backward(dout)
        dout = self.ln_final.backward(dout)
        for block in reversed(self.blocks):
            dout = block.backward(dout)
        dout = self.pos_encoding.backward(dout)
        dout = self.token_embedding.backward(dout)
        return dout

    def parameters(self):
        params = {}
        grads = {}
        for name, layer in [('token_embedding', self.token_embedding),
                            ('pos_encoding', self.pos_encoding),
                            ('ln_final', self.ln_final),
                            ('output', self.output)]:
            p, g = layer.parameters() if hasattr(layer, 'parameters') else (layer.params, layer.grads)
            for key in p:
                params[f'{name}_{key}'] = p[key]
                grads[f'{name}_{key}'] = g[key]
        for i, block in enumerate(self.blocks):
            p, g = block.parameters()
            for key in p:
                params[f'block{i}_{key}'] = p[key]
                grads[f'block{i}_{key}'] = g[key]
        return params, grads

    def zero_grad(self):
        """Обнуление градиентов во всех слоях модели."""
        for layer in [self.token_embedding, self.pos_encoding, self.ln_final, self.output] + self.blocks:
            if hasattr(layer, 'grads'):
                for g in layer.grads.values():
                    g.fill(0)
            if hasattr(layer, 'sub_layers'):
                for sub in layer.sub_layers:
                    for g in sub.grads.values():
                        g.fill(0)