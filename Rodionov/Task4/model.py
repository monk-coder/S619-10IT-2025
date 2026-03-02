import numpy as np


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
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

        N = x.shape[-1]  # d_model

        # Градиенты по gamma и beta
        dgamma = np.sum(dout * x_norm, axis=tuple(range(len(dout.shape) - 1)))
        dbeta = np.sum(dout, axis=tuple(range(len(dout.shape) - 1)))

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

        return dx, dgamma, dbeta


class Linear:
    def __init__(self, in_features, out_features):
        # Инициализация He для лучшей сходимости
        self.W = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        self.b = np.zeros(out_features)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        self.cache['original_shape'] = x.shape
        return x @ self.W + self.b

    def backward(self, dout):
        x = self.cache['x']
        original_shape = self.cache['original_shape']

        # Изменяем форму для матричного умножения
        x_reshaped = x.reshape(-1, x.shape[-1])
        dout_reshaped = dout.reshape(-1, dout.shape[-1])

        # Градиенты
        dW = x_reshaped.T @ dout_reshaped
        db = np.sum(dout_reshaped, axis=0)
        dx = dout_reshaped @ self.W.T

        # Восстанавливаем исходную форму
        dx = dx.reshape(original_shape)

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

        # Softmax
        scores_max = np.max(scores, axis=-1, keepdims=True)
        exp_scores = np.exp(scores - scores_max)
        attn = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

        # Применение attention к значениям
        context = attn @ V

        # Сохраняем для backward
        self.cache = {
            'x': x,
            'Q': Q, 'K': K, 'V': V,
            'attn': attn,
            'scores': scores,
            'scores_max': scores_max,
            'exp_scores': exp_scores,
            'mask': mask,
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
        scores_max = self.cache['scores_max']
        exp_scores = self.cache['exp_scores']
        mask = self.cache['mask']

        # Backward через W_o
        dcontext, dW_o, db_o = self.W_o.backward(dout)

        # Изменяем форму обратно на heads
        dcontext = dcontext.reshape(batch_size, seq_len, self.n_head, self.head_dim)
        dcontext = dcontext.transpose(0, 2, 1, 3)

        # Backward через attention @ V
        dV = attn.transpose(0, 1, 3, 2) @ dcontext
        dattn = dcontext @ V.transpose(0, 1, 3, 2)

        # Backward через softmax
        # Градиент softmax: dL/dscores = dattn * attn * (1 - attn)
        # (упрощенная версия, для полной нужна матрица Якоби)
        dscores = dattn * attn * (1 - attn)

        # Применяем маску к градиентам
        if mask is not None:
            dscores = dscores * mask

        # Масштабируем
        dscores = dscores / np.sqrt(self.head_dim)

        # Backward через умножение Q@K^T
        dQ = dscores @ K
        dK = dscores.transpose(0, 1, 3, 2) @ Q

        # Изменяем форму обратно
        dQ = dQ.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dK = dK.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dV = dV.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)

        # Backward через линейные проекции
        dQ, dW_q, db_q = self.W_q.backward(dQ)
        dK, dW_k, db_k = self.W_k.backward(dK)
        dV, dW_v, db_v = self.W_v.backward(dV)

        # Суммируем градиенты для входа
        dx = dQ + dK + dV

        # Собираем все градиенты параметров
        dW_attn = (dW_q, dW_k, dW_v, dW_o)
        db_attn = (db_q, db_k, db_v, db_o)

        return dx, dW_attn, db_attn


class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.act = GELU()
        self.fc2 = Linear(d_ff, d_model)
        self.cache = {}

    def forward(self, x):
        self.cache['x'] = x
        h = self.fc1.forward(x)
        h_act = self.act.forward(h)
        out = self.fc2.forward(h_act)
        self.cache['h'] = h
        self.cache['h_act'] = h_act
        return out

    def backward(self, dout):
        # Backward через fc2
        dh_act, dW2, db2 = self.fc2.backward(dout)

        # Backward через GELU
        dh = self.act.backward(dh_act)

        # Backward через fc1
        dx, dW1, db1 = self.fc1.backward(dh)

        return dx, (dW1, dW2), (db1, db2)


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.cache = {}

    def forward(self, x, mask):
        # Сохраняем для backward
        self.cache['x_before_attn'] = x

        # Attention с residual connection
        ln1_out = self.ln1.forward(x)
        attn_out = self.attn.forward(ln1_out, mask)
        x = x + attn_out
        self.cache['x_after_attn'] = x
        self.cache['attn_out'] = attn_out
        self.cache['ln1_out'] = ln1_out

        # MLP с residual connection
        self.cache['x_before_mlp'] = x
        ln2_out = self.ln2.forward(x)
        mlp_out = self.mlp.forward(ln2_out)
        x = x + mlp_out
        self.cache['x_after_mlp'] = x
        self.cache['mlp_out'] = mlp_out
        self.cache['ln2_out'] = ln2_out

        return x

    def backward(self, dout):
        # Backward через MLP часть
        dmlp_total = dout  # градиент от выхода

        # Backward через residual connection MLP
        dmlp = dmlp_total  # градиент для MLP пути
        dresidual_mlp = dmlp_total  # градиент для прямого пути

        # Backward через MLP
        dln2_out, dW_mlp, db_mlp = self.mlp.backward(dmlp)
        dln2, dgamma2, dbeta2 = self.ln2.backward(dln2_out)

        # Суммируем с residual
        dx_after_attn = dln2 + dresidual_mlp

        # Backward через Attention часть
        dattn_total = dx_after_attn

        # Backward через residual connection Attention
        dattn = dattn_total  # градиент для attention пути
        dresidual_attn = dattn_total  # градиент для прямого пути

        # Backward через Attention
        dln1_out, dW_attn, db_attn = self.attn.backward(dattn)
        dln1, dgamma1, dbeta1 = self.ln1.backward(dln1_out)

        # Суммируем с residual
        dx = dln1 + dresidual_attn

        return dx, (dgamma1, dbeta1, dgamma2, dbeta2), (dW_attn, dW_mlp), (db_attn, db_mlp)


class TransformerLM:
    def __init__(self, vocab_size, d_model=256, n_head=4, n_layer=4, d_ff=512, max_seq_len=256):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.n_layer = n_layer

        # Эмбеддинги с нормализацией
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

        self.cache['x_emb'] = x_emb
        self.cache['x'] = x

        # Применение блоков трансформера
        block_outputs = []
        for i, block in enumerate(self.blocks):
            x_emb = block.forward(x_emb, self.causal_mask[:, :, :seq_len, :seq_len])
            block_outputs.append(x_emb)

        self.cache['block_outputs'] = block_outputs

        # Выходной слой
        x_norm = self.ln_final.forward(x_emb)
        logits = self.fc_out.forward(x_norm)

        return logits

    def backward(self, dlogits):
        """Полный backward pass"""
        batch_size, seq_len = self.cache['x'].shape

        # Backward через выходной слой
        dln_final, dW_out, db_out = self.fc_out.backward(dlogits)
        dout, dgamma_final, dbeta_final = self.ln_final.backward(dln_final)

        # Backward через блоки трансформера (в обратном порядке)
        for i in range(len(self.blocks) - 1, -1, -1):
            dout = self.blocks[i].backward(dout)[0]

        # Backward через эмбеддинги (градиенты не обновляются напрямую)
        # В реальном обучении здесь нужно обновлять token_embedding

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