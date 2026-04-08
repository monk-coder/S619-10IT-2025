import numpy as np
from typing import Optional


class LayerNorm:
    def __init__(self, d_model: int, eps: float = 1e-5):
        self.d_model = d_model
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.cache = {}
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta = np.zeros_like(self.beta)

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.cache['x'] = x
        self.cache['mean'] = np.mean(x, axis=-1, keepdims=True)
        self.cache['var'] = np.var(x, axis=-1, keepdims=True)
        self.cache['x_hat'] = (x - self.cache['mean']) / np.sqrt(self.cache['var'] + self.eps)
        return self.gamma * self.cache['x_hat'] + self.beta

    def backward(self, dout: np.ndarray) -> np.ndarray:
        batch_size, seq_len, d_model = dout.shape

        self.dgamma = np.sum(dout * self.cache['x_hat'], axis=(0, 1))
        self.dbeta = np.sum(dout, axis=(0, 1))

        dx_hat = dout * self.gamma
        dvar = np.sum(dx_hat * (self.cache['x'] - self.cache['mean']) * -0.5 *
                      (self.cache['var'] + self.eps) ** (-1.5), axis=-1, keepdims=True)
        dmean = np.sum(dx_hat * -1 / np.sqrt(self.cache['var'] + self.eps),
                       axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (self.cache['x'] - self.cache['mean']), axis=-1, keepdims=True)
        dx = dx_hat / np.sqrt(self.cache['var'] + self.eps) + \
             dvar * 2 * (self.cache['x'] - self.cache['mean']) / d_model + \
             dmean / d_model

        return dx


class Linear:
    def __init__(self, in_features: int, out_features: int):
        self.W = np.random.randn(in_features, out_features) * 0.01
        self.b = np.zeros(out_features)
        self.cache = {}
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.cache['x'] = x
        return x @ self.W + self.b

    def backward(self, dout: np.ndarray) -> np.ndarray:
        if self.cache['x'].ndim == 3:
            batch_size, seq_len, in_features = self.cache['x'].shape
            self.dW = self.cache['x'].transpose(0, 2, 1) @ dout
            self.dW = np.sum(self.dW, axis=0)  # Sum over batch
            self.db = np.sum(dout, axis=(0, 1))
            return dout @ self.W.T
        else:
            self.dW = self.cache['x'].T @ dout
            self.db = np.sum(dout, axis=0)
            return dout @ self.W.T


class GELU:
    def __init__(self):
        self.cache = {}

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.cache['x'] = x
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def backward(self, dout: np.ndarray) -> np.ndarray:
        x = self.cache['x']
        tanh_arg = np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)
        tanh_val = np.tanh(tanh_arg)
        gelu_grad = 0.5 * (1 + tanh_val) + \
                    0.5 * x * (1 - tanh_val ** 2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x ** 2)
        return dout * gelu_grad


class MLP:
    def __init__(self, d_model: int, expansion: int = 4):
        self.fc1 = Linear(d_model, d_model * expansion)
        self.gelu = GELU()
        self.fc2 = Linear(d_model * expansion, d_model)

    def forward(self, x: np.ndarray) -> np.ndarray:
        x = self.fc1.forward(x)
        x = self.gelu.forward(x)
        x = self.fc2.forward(x)
        return x

    def backward(self, dout: np.ndarray) -> np.ndarray:
        dout = self.fc2.backward(dout)
        dout = self.gelu.backward(dout)
        dout = self.fc1.backward(dout)
        return dout


class MultiHeadAttention:
    def __init__(self, d_model: int, n_head: int):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_k = d_model // n_head

        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)
        self.W_o = Linear(d_model, d_model)

        self.cache = {}

    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        batch_size, seq_len, _ = x.shape

        Q = self.W_q.forward(x)
        K = self.W_k.forward(x)
        V = self.W_v.forward(x)

        Q = Q.reshape(batch_size, seq_len, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_head, self.d_k).transpose(0, 2, 1, 3)

        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.d_k)

        if mask is not None:
            scores = scores + mask

        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_weights = exp_scores / (np.sum(exp_scores, axis=-1, keepdims=True) + 1e-8)

        out = attn_weights @ V
        out = out.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        out = self.W_o.forward(out)

        self.cache['Q'] = Q
        self.cache['K'] = K
        self.cache['V'] = V
        self.cache['scores'] = scores
        self.cache['attn_weights'] = attn_weights
        self.cache['mask'] = mask

        return out

    def backward(self, dout: np.ndarray) -> np.ndarray:
        batch_size, seq_len, _ = dout.shape

        dout = self.W_o.backward(dout)
        dout = dout.reshape(batch_size, seq_len, self.n_head, self.d_k).transpose(0, 2, 1, 3)

        dV = self.cache['attn_weights'].transpose(0, 1, 3, 2) @ dout
        d_attn = dout @ self.cache['V'].transpose(0, 1, 3, 2)

        d_scores = d_attn / np.sqrt(self.d_k)

        exp_scores = np.exp(self.cache['scores'] - np.max(self.cache['scores'], axis=-1, keepdims=True))
        sum_exp = np.sum(exp_scores, axis=-1, keepdims=True)
        d_scores = exp_scores * (d_scores - np.sum(d_scores * exp_scores, axis=-1, keepdims=True) / sum_exp) / (
                    sum_exp + 1e-8)

        dQ = d_scores @ self.cache['K'] / np.sqrt(self.d_k)
        dK = d_scores.transpose(0, 1, 3, 2) @ self.cache['Q'] / np.sqrt(self.d_k)

        dQ = dQ.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dK = dK.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dV = dV.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)

        dQ = self.W_q.backward(dQ)
        dK = self.W_k.backward(dK)
        dV = self.W_v.backward(dV)

        return dQ + dK + dV


class TransformerBlock:
    def __init__(self, d_model: int, n_head: int):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model)
        self.cache = {}

    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        x_norm = self.ln1.forward(x)
        attn_out = self.attn.forward(x_norm, mask)
        x = x + attn_out

        x_norm = self.ln2.forward(x)
        mlp_out = self.mlp.forward(x_norm)
        x = x + mlp_out

        self.cache['attn_out'] = attn_out
        self.cache['mlp_out'] = mlp_out
        return x

    def backward(self, dout: np.ndarray) -> np.ndarray:
        d_mlp = dout
        d_mlp = self.mlp.backward(d_mlp)
        d_ln2 = d_mlp
        d_residual2 = dout
        d_ln2 = self.ln2.backward(d_ln2)
        d_residual2 += d_ln2

        d_attn = d_residual2
        d_attn = self.attn.backward(d_attn)
        d_ln1 = d_attn
        d_residual1 = d_residual2
        d_ln1 = self.ln1.backward(d_ln1)
        d_residual1 += d_ln1

        return d_residual1


class TransformerLM:
    def __init__(self, vocab_size: int, d_model: int = 128, n_layer: int = 3,
                 n_head: int = 4, max_seq_len: int = 256):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len

        self.token_embedding = np.random.randn(vocab_size, d_model) * 0.01
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * 0.01

        self.blocks = [TransformerBlock(d_model, n_head) for _ in range(n_layer)]
        self.ln_final = LayerNorm(d_model)
        self.lm_head = Linear(d_model, vocab_size)

        self.causal_mask = np.triu(np.ones((max_seq_len, max_seq_len)) * -1e9, k=1)

        self.d_token_embedding = np.zeros_like(self.token_embedding)
        self.d_pos_embedding = np.zeros_like(self.pos_embedding)

    def forward(self, x: np.ndarray) -> np.ndarray:
        batch_size, seq_len = x.shape

        # Embeddings
        token_emb = self.token_embedding[x]
        pos_emb = self.pos_embedding[:seq_len]

        x = token_emb + pos_emb

        # Mask
        mask = self.causal_mask[:seq_len, :seq_len] if seq_len <= self.max_seq_len else None

        # Transformer blocks
        for block in self.blocks:
            x = block.forward(x, mask)

        # Final layer
        x = self.ln_final.forward(x)
        logits = self.lm_head.forward(x)

        return logits

    def backward(self, dlogits: np.ndarray, x: np.ndarray) -> None:
        """Backward pass with proper embedding gradients"""
        dout = self.lm_head.backward(dlogits)
        dout = self.ln_final.backward(dout)

        for block in reversed(self.blocks):
            dout = block.backward(dout)

        # Gradient for embeddings (dout shape: batch, seq_len, d_model)
        # We need to propagate gradients to token_embedding
        self.d_token_embedding = np.zeros_like(self.token_embedding)

        # For each position in sequence, add gradient to the corresponding token
        for b in range(dout.shape[0]):  # batch
            for t in range(dout.shape[1]):  # sequence position
                token_id = self.cache['input_tokens'][b, t]
                self.d_token_embedding[token_id] += dout[b, t]

        # Position embedding gradients
        self.d_pos_embedding = np.zeros_like(self.pos_embedding)
        seq_len = dout.shape[1]
        self.d_pos_embedding[:seq_len] = np.sum(dout, axis=(0, 1))