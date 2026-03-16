# model.py
import numpy as np


# ==================== УТИЛИТЫ ====================
def softmax(x, axis=-1):
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))


def gelu_derivative(x):
    tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3))
    return 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out ** 2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x ** 2)


def create_causal_mask(size):
    mask = np.triu(np.ones((size, size)) * -1e9, k=1)
    return mask


# ==================== LAYER NORM ====================
class LayerNorm:
    def __init__(self, dim, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(dim)
        self.beta = np.zeros(dim)
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta = np.zeros_like(self.beta)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        self.cache['mean'] = np.mean(x, axis=-1, keepdims=True)
        self.cache['var'] = np.var(x, axis=-1, keepdims=True)
        self.cache['x_norm'] = (x - self.cache['mean']) / np.sqrt(self.cache['var'] + self.eps)
        return self.gamma * self.cache['x_norm'] + self.beta

    def backward(self, dout):
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']

        N = x.shape[-1]
        self.dgamma = np.sum(dout * x_norm, axis=(0, 1))
        self.dbeta = np.sum(dout, axis=(0, 1))

        dx_norm = dout * self.gamma
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps) ** (-1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)

        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / N + dmean / N
        return dx

    def get_params(self):
        return [(self.gamma, self.dgamma), (self.beta, self.dbeta)]

    def zero_grad(self):
        self.dgamma.fill(0)
        self.dbeta.fill(0)


# ==================== ATTENTION ====================
class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_k = d_model // n_head

        scale = 1 / np.sqrt(d_model)
        self.W_q = np.random.randn(d_model, d_model) * scale
        self.W_k = np.random.randn(d_model, d_model) * scale
        self.W_v = np.random.randn(d_model, d_model) * scale
        self.W_o = np.random.randn(d_model, d_model) * scale

        self.dW_q = np.zeros_like(self.W_q)
        self.dW_k = np.zeros_like(self.W_k)
        self.dW_v = np.zeros_like(self.W_v)
        self.dW_o = np.zeros_like(self.W_o)
        self.cache = {}

    def _reshape_for_heads(self, x):
        B, T, D = x.shape
        x = x.reshape(B, T, self.n_head, self.d_k)
        return x.transpose(0, 2, 1, 3)  # (B, n_head, T, d_k)

    def _reshape_from_heads(self, x):
        B, n_head, T, d_k = x.shape
        x = x.transpose(0, 2, 1, 3)  # (B, T, n_head, d_k)
        return x.reshape(B, T, self.d_model)

    def forward(self, x, mask=None):
        B, T, D = x.shape
        self.cache['x'] = x
        self.cache['mask'] = mask
        self.cache['B'] = B
        self.cache['T'] = T

        # Линейные проекции
        Q = x @ self.W_q  # (B, T, D)
        K = x @ self.W_k
        V = x @ self.W_v
        self.cache['Q'] = Q
        self.cache['K'] = K
        self.cache['V'] = V

        # Reshape для голов
        Q = self._reshape_for_heads(Q)  # (B, n_head, T, d_k)
        K = self._reshape_for_heads(K)
        V = self._reshape_for_heads(V)
        self.cache['Q_heads'] = Q
        self.cache['K_heads'] = K
        self.cache['V_heads'] = V

        # Scaled Dot-Product Attention
        scores = (Q @ K.transpose(0, 1, 3, 2)) / np.sqrt(self.d_k)  # (B, n_head, T, T)
        if mask is not None:
            scores = scores + mask

        attn_weights = softmax(scores, axis=-1)
        self.cache['attn_weights'] = attn_weights

        context = attn_weights @ V  # (B, n_head, T, d_k)
        self.cache['context_heads'] = context

        # Объединение голов
        context = self._reshape_from_heads(context)  # (B, T, D)
        self.cache['context'] = context

        # Финальная проекция
        output = context @ self.W_o
        return output

    def backward(self, dout):
        B = self.cache['B']
        T = self.cache['T']
        D = self.d_model

        # Градиент для W_o
        context = self.cache['context']
        self.dW_o = context.reshape(-1, D).T @ dout.reshape(-1, D)

        # Градиент для context
        dcontext = dout @ self.W_o.T  # (B, T, D)
        dcontext = self._reshape_for_heads(dcontext)  # (B, n_head, T, d_k)

        # Получаем сохраненные значения
        attn_weights = self.cache['attn_weights']  # (B, n_head, T, T)
        V_heads = self.cache['V_heads']  # (B, n_head, T, d_k)
        Q_heads = self.cache['Q_heads']
        K_heads = self.cache['K_heads']

        # Градиент для V
        dV = attn_weights.transpose(0, 1, 3, 2) @ dcontext  # (B, n_head, T, d_k)

        # Градиент для attn_weights
        dattn = dcontext @ V_heads.transpose(0, 1, 3, 2)  # (B, n_head, T, T)

        # Градиент для scores (через softmax)
        dscores = attn_weights * (dattn - np.sum(dattn * attn_weights, axis=-1, keepdims=True))
        dscores = dscores / np.sqrt(self.d_k)

        # Градиенты для Q и K
        dQ = dscores @ K_heads  # (B, n_head, T, d_k)
        dK = dscores.transpose(0, 1, 3, 2) @ Q_heads  # (B, n_head, T, d_k)

        # Возвращаем к исходной размерности
        dQ = self._reshape_from_heads(dQ)  # (B, T, D)
        dK = self._reshape_from_heads(dK)
        dV = self._reshape_from_heads(dV)

        # Градиенты для линейных проекций
        x = self.cache['x']
        self.dW_q = x.reshape(-1, D).T @ dQ.reshape(-1, D)
        self.dW_k = x.reshape(-1, D).T @ dK.reshape(-1, D)
        self.dW_v = x.reshape(-1, D).T @ dV.reshape(-1, D)

        # Градиент для входа
        dx = (dQ @ self.W_q.T) + (dK @ self.W_k.T) + (dV @ self.W_v.T)
        return dx

    def get_params(self):
        return [(self.W_q, self.dW_q), (self.W_k, self.dW_k), (self.W_v, self.dW_v), (self.W_o, self.dW_o)]

    def zero_grad(self):
        self.dW_q.fill(0)
        self.dW_k.fill(0)
        self.dW_v.fill(0)
        self.dW_o.fill(0)


# ==================== MLP ====================
class MLP:
    def __init__(self, d_model, d_ff):
        scale1 = 1 / np.sqrt(d_model)
        scale2 = 1 / np.sqrt(d_ff)

        self.W1 = np.random.randn(d_model, d_ff) * scale1
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * scale2
        self.b2 = np.zeros(d_model)

        self.dW1 = np.zeros_like(self.W1)
        self.db1 = np.zeros_like(self.b1)
        self.dW2 = np.zeros_like(self.W2)
        self.db2 = np.zeros_like(self.b2)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        hidden = x @ self.W1 + self.b1
        self.cache['hidden'] = hidden
        act = gelu(hidden)
        self.cache['act'] = act
        output = act @ self.W2 + self.b2
        return output

    def backward(self, dout):
        x = self.cache['x']
        hidden = self.cache['hidden']
        act = self.cache['act']

        # Градиент для W2 и b2
        self.dW2 = act.reshape(-1, act.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        self.db2 = np.sum(dout, axis=(0, 1))

        # Градиент для act
        dact = dout @ self.W2.T

        # Градиент для hidden (через GELU)
        dhidden = dact * gelu_derivative(hidden)

        # Градиент для W1 и b1
        self.dW1 = x.reshape(-1, x.shape[-1]).T @ dhidden.reshape(-1, dhidden.shape[-1])
        self.db1 = np.sum(dhidden, axis=(0, 1))

        # Градиент для входа
        dx = dhidden @ self.W1.T
        return dx

    def get_params(self):
        return [(self.W1, self.dW1), (self.b1, self.db1), (self.W2, self.dW2), (self.b2, self.db2)]

    def zero_grad(self):
        self.dW1.fill(0)
        self.db1.fill(0)
        self.dW2.fill(0)
        self.db2.fill(0)


# ==================== TRANSFORMER BLOCK ====================
class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.cache = {}

    def forward(self, x, mask=None):
        self.cache['x'] = x

        # Первый residual block
        ln1_out = self.ln1.forward(x)
        attn_out = self.attn.forward(ln1_out, mask)
        x1 = x + attn_out
        self.cache['x1'] = x1

        # Второй residual block
        ln2_out = self.ln2.forward(x1)
        mlp_out = self.mlp.forward(ln2_out)
        x2 = x1 + mlp_out
        self.cache['x2'] = x2

        return x2

    def backward(self, dout):
        x1 = self.cache['x1']

        # Второй residual block
        dmlp = dout
        dln2 = self.mlp.backward(dmlp)
        dresidual2 = self.ln2.backward(dln2)
        dout1 = dout + dresidual2

        # Первый residual block
        dattn = dout1
        dln1 = self.attn.backward(dattn)
        dresidual1 = self.ln1.backward(dln1)
        dx = dout1 + dresidual1

        return dx

    def get_params(self):
        params = []
        params.extend(self.ln1.get_params())
        params.extend(self.attn.get_params())
        params.extend(self.ln2.get_params())
        params.extend(self.mlp.get_params())
        return params

    def zero_grad(self):
        self.ln1.zero_grad()
        self.attn.zero_grad()
        self.ln2.zero_grad()
        self.mlp.zero_grad()
        self.cache = {}


# ==================== MAIN MODEL ====================
class TransformerLM:
    def __init__(self, vocab_size, d_model, n_head, n_layer, max_seq_len, d_ff=None):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_head = n_head
        self.n_layer = n_layer
        self.max_seq_len = max_seq_len
        self.d_ff = d_ff if d_ff is not None else 4 * d_model

        # Эмбеддинги
        scale = 1 / np.sqrt(d_model)
        self.token_embedding = np.random.randn(vocab_size, d_model) * scale
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * scale

        # Блоки
        self.blocks = [TransformerBlock(d_model, n_head, self.d_ff) for _ in range(n_layer)]

        # Выходной слой
        self.ln_final = LayerNorm(d_model)
        self.output_proj = np.random.randn(d_model, vocab_size) * scale

        # Градиенты
        self.d_token_embedding = np.zeros_like(self.token_embedding)
        self.d_pos_embedding = np.zeros_like(self.pos_embedding)
        self.d_output_proj = np.zeros_like(self.output_proj)

        self.cache = {}
        self.causal_mask = create_causal_mask(max_seq_len)

    def forward(self, x):
        B, T = x.shape
        assert T <= self.max_seq_len

        self.cache['x'] = x
        self.cache['T'] = T
        self.cache['B'] = B

        # Эмбеддинги
        token_emb = self.token_embedding[x]  # (B, T, d_model)
        pos_emb = self.pos_embedding[:T].reshape(1, T, self.d_model)  # (1, T, d_model)
        x = token_emb + pos_emb

        self.cache['token_emb'] = token_emb
        self.cache['pos_emb'] = pos_emb
        self.cache['embed_out'] = x

        # Блоки
        for i, block in enumerate(self.blocks):
            x = block.forward(x, self.causal_mask[:T, :T])
            self.cache[f'block_{i}_out'] = x

        # Выход
        x = self.ln_final.forward(x)
        self.cache['final_norm'] = x
        logits = x @ self.output_proj
        return logits

    def backward(self, dlogits):
        B, T, V = dlogits.shape
        D = self.d_model

        # Градиент для выходной проекции
        final_norm = self.cache['final_norm']
        self.d_output_proj = final_norm.reshape(-1, D).T @ dlogits.reshape(-1, V)

        # Градиент для финальной нормализации
        dx = dlogits @ self.output_proj.T
        dx = self.ln_final.backward(dx)

        # Блоки в обратном порядке
        for i in reversed(range(self.n_layer)):
            dx = self.blocks[i].backward(dx)

        # Градиенты для эмбеддингов
        x_indices = self.cache['x']
        T = self.cache['T']
        B = self.cache['B']

        # Позиционные эмбеддинги
        self.d_pos_embedding[:T] += np.sum(dx, axis=0)

        # Токен эмбеддинги
        for b in range(B):
            for t in range(T):
                self.d_token_embedding[x_indices[b, t]] += dx[b, t]

        return dx

    def get_params(self):
        params = [
            (self.token_embedding, self.d_token_embedding),
            (self.pos_embedding, self.d_pos_embedding),
            (self.output_proj, self.d_output_proj)
        ]
        params.extend(self.ln_final.get_params())
        for block in self.blocks:
            params.extend(block.get_params())
        return params

    def zero_grad(self):
        self.d_token_embedding.fill(0)
        self.d_pos_embedding.fill(0)
        self.d_output_proj.fill(0)
        self.ln_final.zero_grad()
        for block in self.blocks:
            block.zero_grad()
        self.cache = {}

    def generate(self, prompt, max_new_tokens, temperature=1.0, top_k=None):
        generated = list(prompt)

        for _ in range(max_new_tokens):
            context = generated[-self.max_seq_len:]
            x = np.array([context])
            logits = self.forward(x)

            next_token_logits = logits[0, -1, :] / temperature

            if top_k is not None:
                indices = np.argsort(next_token_logits)[-top_k:]
                mask = np.ones_like(next_token_logits) * -1e9
                mask[indices] = 0
                next_token_logits = next_token_logits + mask

            probs = softmax(next_token_logits)
            next_token = np.random.choice(len(probs), p=probs)
            generated.append(next_token)

        return np.array(generated)