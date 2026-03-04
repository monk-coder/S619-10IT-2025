import numpy as np


def softmax(x, axis=-1):
    """
    Стабильный softmax
    """
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.cache = {}
        self.dgamma = None
        self.dbeta = None

    def forward(self, x):
        self.cache['x'] = x.copy() if hasattr(x, 'copy') else x
        self.cache['mean'] = np.mean(x, axis=-1, keepdims=True)
        self.cache['var'] = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - self.cache['mean']) / np.sqrt(self.cache['var'] + self.eps)
        self.cache['x_norm'] = x_norm
        return self.gamma * x_norm + self.beta

    def backward(self, dout):
        x = self.cache['x']
        mean = self.cache['mean']
        var = self.cache['var']
        x_norm = self.cache['x_norm']

        N = x.shape[-1]

        # Сохраняем градиенты
        axes = tuple(range(len(dout.shape) - 1))
        self.dgamma = np.sum(dout * x_norm, axis=axes)
        self.dbeta = np.sum(dout, axis=axes)

        # Градиент по x_norm
        dx_norm = dout * self.gamma

        # Градиент по var
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps) ** (-1.5),
                      axis=-1, keepdims=True)

        # Градиент по mean
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True)
        dmean += dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)

        # Градиент по x
        dx = dx_norm / np.sqrt(var + self.eps)
        dx += dvar * 2 * (x - mean) / N
        dx += dmean / N

        return dx


class Linear:
    def __init__(self, in_features, out_features):
        # Инициализация He для лучшей сходимости
        self.W = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        self.b = np.zeros(out_features)
        self.cache = {}
        # Добавляем хранение градиентов
        self.dW = None
        self.db = None

    def forward(self, x):
        self.cache['x'] = x.copy() if hasattr(x, 'copy') else x
        self.cache['original_shape'] = x.shape
        return x @ self.W + self.b

    def backward(self, dout):
        x = self.cache['x']
        original_shape = self.cache['original_shape']

        # Изменяем форму для матричного умножения
        x_reshaped = x.reshape(-1, x.shape[-1])
        dout_reshaped = dout.reshape(-1, dout.shape[-1])

        # Сохраняем градиенты
        self.dW = x_reshaped.T @ dout_reshaped
        self.db = np.sum(dout_reshaped, axis=0)
        dx = dout_reshaped @ self.W.T

        # Восстанавливаем исходную форму
        dx = dx.reshape(original_shape)

        # Очищаем кэш, чтобы не накапливать память
        self.cache = {}

        return dx


class GELU:
    def __init__(self):
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x.copy() if hasattr(x, 'copy') else x
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def backward(self, dout):
        x = self.cache['x']
        tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3))
        sech2 = 1 - tanh_out ** 2
        grad = 0.5 * (1 + tanh_out) + 0.5 * x * sech2 * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x ** 2)

        # Очищаем кэш
        self.cache = {}

        return dout * grad


class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head
        assert self.head_dim * n_head == d_model, "d_model must be divisible by n_head"

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
            # Применяем маску (где mask=0, ставим -inf)
            scores = np.where(mask == 1, scores, -1e9)

        # Softmax с использованием нашей функции
        attn = softmax(scores, axis=-1)

        # Применение attention к значениям
        context = attn @ V

        # Сохраняем для backward (делаем копии)
        self.cache = {
            'x': x.copy() if hasattr(x, 'copy') else x,
            'Q': Q.copy() if hasattr(Q, 'copy') else Q,
            'K': K.copy() if hasattr(K, 'copy') else K,
            'V': V.copy() if hasattr(V, 'copy') else V,
            'attn': attn.copy() if hasattr(attn, 'copy') else attn,
            'scores': scores.copy() if hasattr(scores, 'copy') else scores,
            'mask': mask.copy() if mask is not None and hasattr(mask, 'copy') else mask,
            'batch_size': batch_size,
            'seq_len': seq_len
        }

        # Объединение голов
        context = context.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        out = self.W_o.forward(context)

        return out

    def backward(self, dout):
        # Получаем сохраненные значения
        batch_size = self.cache['batch_size']
        seq_len = self.cache['seq_len']
        Q = self.cache['Q']
        K = self.cache['K']
        V = self.cache['V']
        attn = self.cache['attn']
        scores = self.cache['scores']
        mask = self.cache['mask']

        # Backward через W_o
        dcontext = self.W_o.backward(dout)

        # Изменяем форму обратно на heads
        dcontext = dcontext.reshape(batch_size, seq_len, self.n_head, self.head_dim)
        dcontext = dcontext.transpose(0, 2, 1, 3)

        # Backward через attention @ V
        dV = attn.transpose(0, 1, 3, 2) @ dcontext
        dattn = dcontext @ V.transpose(0, 1, 3, 2)

        # Backward через softmax
        dscores = np.zeros_like(scores)

        # Для каждой позиции вычисляем градиент через softmax
        for b in range(batch_size):
            for h in range(self.n_head):
                s = attn[b, h]
                d = dattn[b, h]
                sum_ds = np.sum(d * s, axis=-1, keepdims=True)
                dscores[b, h] = s * (d - sum_ds)

        # Масштабируем
        dscores = dscores / np.sqrt(self.head_dim)

        # Применяем маску к градиентам если нужно
        if mask is not None:
            dscores = dscores * mask

        # Backward через умножение Q@K^T
        dQ = dscores @ K
        dK = dscores.transpose(0, 1, 3, 2) @ Q

        # Изменяем форму обратно
        dQ = dQ.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dK = dK.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dV = dV.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)

        # Backward через линейные проекции
        dx_q = self.W_q.backward(dQ)
        dx_k = self.W_k.backward(dK)
        dx_v = self.W_v.backward(dV)

        # Суммируем градиенты для входа
        dx = dx_q + dx_k + dx_v

        # Очищаем кэш
        self.cache = {}

        return dx


class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.act = GELU()
        self.fc2 = Linear(d_ff, d_model)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x.copy() if hasattr(x, 'copy') else x
        h = self.fc1.forward(x)
        h_act = self.act.forward(h)
        out = self.fc2.forward(h_act)
        return out

    def backward(self, dout):
        # Backward через fc2
        dh_act = self.fc2.backward(dout)

        # Backward через GELU
        dh = self.act.backward(dh_act)

        # Backward через fc1
        dx = self.fc1.backward(dh)

        # Очищаем кэш
        self.cache = {}

        return dx


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.cache = {}

    def forward(self, x, mask):
        # Сохраняем для backward
        self.cache['x_before_attn'] = x.copy() if hasattr(x, 'copy') else x

        # Attention с residual connection
        ln1_out = self.ln1.forward(x)
        attn_out = self.attn.forward(ln1_out, mask)
        x = x + attn_out
        self.cache['x_after_attn'] = x.copy() if hasattr(x, 'copy') else x
        self.cache['attn_out'] = attn_out
        self.cache['ln1_out'] = ln1_out

        # MLP с residual connection
        self.cache['x_before_mlp'] = x.copy() if hasattr(x, 'copy') else x
        ln2_out = self.ln2.forward(x)
        mlp_out = self.mlp.forward(ln2_out)
        x = x + mlp_out
        self.cache['x_after_mlp'] = x.copy() if hasattr(x, 'copy') else x
        self.cache['mlp_out'] = mlp_out
        self.cache['ln2_out'] = ln2_out

        return x

    def backward(self, dout):
        # Backward через residual connection (для последнего выхода)
        dmlp = dout
        dresidual_mlp = dout

        # Backward через MLP
        dln2_out = self.mlp.backward(dmlp)
        dln2 = self.ln2.backward(dln2_out)

        # Суммируем с residual
        dx_after_attn = dln2 + dresidual_mlp

        # Backward через residual connection Attention
        dattn = dx_after_attn
        dresidual_attn = dx_after_attn

        # Backward через Attention
        dln1_out = self.attn.backward(dattn)
        dln1 = self.ln1.backward(dln1_out)

        # Суммируем с residual
        dx = dln1 + dresidual_attn

        # Очищаем кэш
        self.cache = {}

        return dx


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
        self.register_causal_mask(max_seq_len)

        self.cache = {}
        self.training = True

    def register_causal_mask(self, max_seq_len):
        """Создает и сохраняет причинную маску"""
        self.causal_mask = np.tril(np.ones((max_seq_len, max_seq_len))).reshape(1, 1, max_seq_len, max_seq_len)

    def forward(self, x):
        batch_size, seq_len = x.shape
        assert seq_len <= self.max_seq_len, f"Sequence length {seq_len} exceeds max_seq_len {self.max_seq_len}"

        # Эмбеддинги
        x_emb = self.token_embedding[x]
        x_emb = x_emb + self.pos_embedding[:seq_len]

        self.cache['x_emb'] = x_emb.copy() if hasattr(x_emb, 'copy') else x_emb
        self.cache['x'] = x.copy() if hasattr(x, 'copy') else x

        # Применение блоков трансформера
        for i, block in enumerate(self.blocks):
            x_emb = block.forward(x_emb, self.causal_mask[:, :, :seq_len, :seq_len])

        # Выходной слой
        x_norm = self.ln_final.forward(x_emb)
        logits = self.fc_out.forward(x_norm)

        return logits

    def backward(self, dlogits):
        """Полный backward pass"""
        # Backward через выходной слой
        dln_final = self.fc_out.backward(dlogits)
        dout = self.ln_final.backward(dln_final)

        # Backward через блоки трансформера (в обратном порядке)
        for i in range(len(self.blocks) - 1, -1, -1):
            dout = self.blocks[i].backward(dout)

        # Очищаем кэш
        self.cache = {}

        return dout

    def parameters(self):
        """Возвращает список всех параметров модели"""
        params = []
        # Эмбеддинги
        params.append(self.token_embedding)
        params.append(self.pos_embedding)

        # Параметры блоков
        for block in self.blocks:
            # LayerNorm параметры
            params.append(block.ln1.gamma)
            params.append(block.ln1.beta)
            params.append(block.ln2.gamma)
            params.append(block.ln2.beta)

            # Attention параметры
            params.append(block.attn.W_q.W)
            params.append(block.attn.W_q.b)
            params.append(block.attn.W_k.W)
            params.append(block.attn.W_k.b)
            params.append(block.attn.W_v.W)
            params.append(block.attn.W_v.b)
            params.append(block.attn.W_o.W)
            params.append(block.attn.W_o.b)

            # MLP параметры
            params.append(block.mlp.fc1.W)
            params.append(block.mlp.fc1.b)
            params.append(block.mlp.fc2.W)
            params.append(block.mlp.fc2.b)

        # Финальные параметры
        params.append(self.ln_final.gamma)
        params.append(self.ln_final.beta)
        params.append(self.fc_out.W)
        params.append(self.fc_out.b)

        return params

    def train(self):
        self.training = True

    def eval(self):
        self.training = False