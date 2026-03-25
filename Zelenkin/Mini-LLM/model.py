import numpy as np


class LayerNorm:
    """Layer Normalization"""

    def __init__(self, dim, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(dim, dtype=np.float32)
        self.beta = np.zeros(dim, dtype=np.float32)
        self.dgamma = None
        self.dbeta = None
        self.cache = None

    def forward(self, x):
        self.cache = x.copy()
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        self.x_norm = (x - mean) / np.sqrt(var + self.eps)
        out = self.gamma * self.x_norm + self.beta
        return out

    def backward(self, dout):
        N, D = dout.shape
        x = self.cache
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)

        dgamma = np.sum(dout * x_norm, axis=0)
        dbeta = np.sum(dout, axis=0)

        dx_norm = dout * self.gamma
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps) ** -1.5, axis=-1, keepdims=True)
        dmean = np.sum(dx_norm * -1 / np.sqrt(var + self.eps), axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)
        dx = dx_norm / np.sqrt(var + self.eps) + dvar * 2 * (x - mean) / N + dmean / N

        self.dgamma = dgamma
        self.dbeta = dbeta
        return dx


class Linear:
    """Полносвязный слой"""

    def __init__(self, in_features, out_features):
        self.W = np.random.randn(in_features, out_features) * 0.01
        self.b = np.zeros(out_features)
        self.dW = None
        self.db = None
        self.cache = None

    def forward(self, x):
        self.cache = x
        return x @ self.W + self.b

    def backward(self, dout):
        self.dW = self.cache.T @ dout
        self.db = np.sum(dout, axis=0)
        dx = dout @ self.W.T
        return dx

    def update(self, learning_rate):
        self.W -= learning_rate * self.dW
        self.b -= learning_rate * self.db


class Embedding:
    """Слой эмбеддингов"""

    def __init__(self, vocab_size, d_model):
        self.W = np.random.randn(vocab_size, d_model) * 0.01
        self.dW = None
        self.cache = None

    def forward(self, x):
        self.cache = x
        return self.W[x]

    def backward(self, dout):
        self.dW = np.zeros_like(self.W)
        np.add.at(self.dW, self.cache, dout)
        return None

    def update(self, learning_rate):
        self.W -= learning_rate * self.dW


class MultiHeadAttention:
    """Multi-Head Self-Attention с causal mask"""

    def __init__(self, d_model, n_head, block_size, dropout=0.1):
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head
        self.block_size = block_size

        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)
        self.W_o = Linear(d_model, d_model)

        # Causal mask
        self.mask = np.tril(np.ones((block_size, block_size))).reshape(1, 1, block_size, block_size)
        self.dropout = dropout
        self.cache = None

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        Q = self.W_q.forward(x)
        K = self.W_k.forward(x)
        V = self.W_v.forward(x)

        # Reshape for multi-head
        Q = Q.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)

        # Attention scores
        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.head_dim)

        # Apply causal mask
        scores = scores * self.mask[:, :, :seq_len, :seq_len] + \
                 (1 - self.mask[:, :, :seq_len, :seq_len]) * -1e9

        # Softmax
        attn = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn = attn / np.sum(attn, axis=-1, keepdims=True)

        # Apply dropout (simplified)
        if self.dropout > 0:
            mask = np.random.binomial(1, 1 - self.dropout, attn.shape) / (1 - self.dropout)
            attn = attn * mask

        # Apply attention to values
        out = attn @ V
        out = out.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        out = self.W_o.forward(out)

        self.cache = (Q, K, V, attn, scores)
        return out

    def backward(self, dout):
        # Simplified backward pass (for educational purposes)
        # In a full implementation, we would compute gradients for all parameters
        dx = dout
        return dx

    def update(self, learning_rate):
        self.W_q.update(learning_rate)
        self.W_k.update(learning_rate)
        self.W_v.update(learning_rate)
        self.W_o.update(learning_rate)


class MLP:
    """MLP с GELU активацией"""

    def __init__(self, d_model, dropout=0.1):
        self.fc1 = Linear(d_model, 4 * d_model)
        self.fc2 = Linear(4 * d_model, d_model)
        self.dropout = dropout
        self.cache = None

    def gelu(self, x):
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def forward(self, x):
        x = self.fc1.forward(x)
        self.cache = x
        x = self.gelu(x)
        x = self.fc2.forward(x)
        if self.dropout > 0:
            mask = np.random.binomial(1, 1 - self.dropout, x.shape) / (1 - self.dropout)
            x = x * mask
        return x

    def backward(self, dout):
        dx = self.fc2.backward(dout)
        # Simplified: gelu gradient
        dx = dx * (0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (self.cache + 0.044715 * self.cache ** 3))) +
                   0.5 * self.cache * (
                               1 - np.tanh(np.sqrt(2 / np.pi) * (self.cache + 0.044715 * self.cache ** 3)) ** 2) *
                   np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * self.cache ** 2))
        dx = self.fc1.backward(dx)
        return dx

    def update(self, learning_rate):
        self.fc1.update(learning_rate)
        self.fc2.update(learning_rate)


class TransformerBlock:
    """Один блок Transformer"""

    def __init__(self, d_model, n_head, block_size, dropout=0.1):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head, block_size, dropout)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, dropout)
        self.cache = None

    def forward(self, x):
        # Self-attention with residual
        x_norm = self.ln1.forward(x)
        attn_out = self.attn.forward(x_norm)
        x = x + attn_out

        # MLP with residual
        x_norm = self.ln2.forward(x)
        mlp_out = self.mlp.forward(x_norm)
        x = x + mlp_out

        self.cache = x
        return x

    def backward(self, dout):
        dx = dout
        return dx

    def update(self, learning_rate):
        self.ln1.update(learning_rate)
        self.attn.update(learning_rate)
        self.ln2.update(learning_rate)
        self.mlp.update(learning_rate)


class TransformerLM:
    """Decoder-only Transformer Language Model"""

    def __init__(self, config):
        self.config = config
        self.token_embedding = Embedding(config.vocab_size, config.d_model)
        self.pos_embedding = Embedding(config.block_size, config.d_model)

        self.blocks = [
            TransformerBlock(config.d_model, config.n_head, config.block_size, config.dropout)
            for _ in range(config.n_layer)
        ]

        self.ln_f = LayerNorm(config.d_model)
        self.lm_head = Linear(config.d_model, config.vocab_size)

        self.cache = None

    def forward(self, x):
        batch_size, seq_len = x.shape

        # Token embeddings
        token_emb = self.token_embedding.forward(x)

        # Position embeddings
        positions = np.arange(seq_len)[None, :].repeat(batch_size, axis=0)
        pos_emb = self.pos_embedding.forward(positions)

        x = token_emb + pos_emb

        # Transformer blocks
        for block in self.blocks:
            x = block.forward(x)

        x = self.ln_f.forward(x)
        logits = self.lm_head.forward(x)

        self.cache = x
        return logits

    def backward(self, dlogits):
        dx = self.lm_head.backward(dlogits)
        dx = self.ln_f.backward(dx)

        for block in reversed(self.blocks):
            dx = block.backward(dx)

        return dx

    def update(self, learning_rate):
        self.token_embedding.update(learning_rate)
        self.pos_embedding.update(learning_rate)
        for block in self.blocks:
            block.update(learning_rate)
        self.ln_f.update(learning_rate)
        self.lm_head.update(learning_rate)

    def generate(self, prompt_tokens, max_new_tokens, temperature=1.0, top_k=None):
        """Генерация текста"""
        context = prompt_tokens.copy()

        for _ in range(max_new_tokens):
            # Обрезаем до block_size
            context_crop = context[-self.config.block_size:]

            # Forward pass
            logits = self.forward(context_crop[None, :])
            logits = logits[0, -1, :] / temperature

            # Top-k sampling
            if top_k is not None:
                indices = np.argpartition(logits, -top_k)[-top_k:]
                logits_filtered = np.full_like(logits, -np.inf)
                logits_filtered[indices] = logits[indices]
                logits = logits_filtered

            # Softmax и sampling
            probs = np.exp(logits - np.max(logits))
            probs = probs / np.sum(probs)
            next_token = np.random.choice(len(probs), p=probs)

            context = np.append(context, next_token)

        return context

    def compute_loss(self, logits, targets):
        """Cross-entropy loss"""
        batch_size, seq_len, vocab_size = logits.shape

        # Reshape
        logits_flat = logits.reshape(-1, vocab_size)
        targets_flat = targets.reshape(-1)

        # Softmax cross-entropy
        exp_logits = np.exp(logits_flat - np.max(logits_flat, axis=-1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

        # Loss
        correct = probs[np.arange(len(targets_flat)), targets_flat]
        loss = -np.log(correct + 1e-8)

        # Gradient (dlogits)
        dlogits = probs.copy()
        dlogits[np.arange(len(targets_flat)), targets_flat] -= 1
        dlogits = dlogits.reshape(batch_size, seq_len, vocab_size) / batch_size

        return np.mean(loss), dlogits