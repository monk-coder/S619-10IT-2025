import numpy as np
from constants import N_LAYERS, N_HEADS, D_MODEL, D_FF, MAX_SEQ_LEN, DROPOUT_RATE


class LayerNorm:
    def __init__(self, dim: int, eps: float = 1e-5):
        self.dim = dim
        self.eps = eps
        self.gamma = np.ones((1, 1, dim))
        self.beta = np.zeros((1, 1, dim))
        self.grad_gamma = np.zeros_like(self.gamma)
        self.grad_beta = np.zeros_like(self.beta)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        self.x = x
        self.mean = np.mean(x, axis=-1, keepdims=True)
        self.var = np.var(x, axis=-1, keepdims=True)
        self.std = np.sqrt(self.var + self.eps)
        self.x_norm = (x - self.mean) / self.std
        return self.gamma * self.x_norm + self.beta
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        N = self.x.shape[-1]
        
        self.grad_gamma = np.sum(grad_output * self.x_norm, axis=(0, 1), keepdims=True)
        self.grad_beta = np.sum(grad_output, axis=(0, 1), keepdims=True)
        
        grad_x_norm = grad_output * self.gamma
        grad_var = np.sum(grad_x_norm * (self.x - self.mean) * -0.5 * self.std**-3, axis=-1, keepdims=True)
        grad_mean = np.sum(grad_x_norm * -1.0 / self.std, axis=-1, keepdims=True) + grad_var * np.mean(-2.0 * (self.x - self.mean), axis=-1, keepdims=True)
        
        grad_input = grad_x_norm / self.std + grad_var * 2.0 * (self.x - self.mean) / N + grad_mean / N
        return grad_input


class MultiHeadAttention:
    def __init__(self, d_model: int, n_heads: int, max_seq_len: int):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.d_v = d_model // n_heads
        
        self.W_q = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_k = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_v = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_o = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        
        self.grad_W_q = np.zeros_like(self.W_q)
        self.grad_W_k = np.zeros_like(self.W_k)
        self.grad_W_v = np.zeros_like(self.W_v)
        self.grad_W_o = np.zeros_like(self.W_o)
        
        self.causal_mask = np.triu(np.ones((max_seq_len, max_seq_len)), k=1) * -1e9
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        batch_size, seq_len = x.shape[0], x.shape[1]
        
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        Q = Q.reshape(batch_size, seq_len, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_heads, self.d_v).transpose(0, 2, 1, 3)
        
        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.d_k)
        scores[:, :, :, :seq_len] += self.causal_mask[:seq_len, :seq_len]
        
        attn_weights = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_weights = attn_weights / np.sum(attn_weights, axis=-1, keepdims=True)
        
        self.attn_weights = attn_weights
        self.Q, self.K, self.V = Q, K, V
        self.x = x
        self.batch_size = batch_size
        self.seq_len = seq_len
        
        context = attn_weights @ V
        context = context.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        output = context @ self.W_o
        
        return output
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        batch_size, seq_len = self.batch_size, self.seq_len
        
        grad_context = grad_output @ self.W_o.T
        grad_context = grad_context.reshape(batch_size, seq_len, self.n_heads, self.d_v).transpose(0, 2, 1, 3)
        
        grad_V = self.attn_weights.transpose(0, 1, 3, 2) @ grad_context
        grad_attn_weights = grad_context @ self.V.transpose(0, 1, 3, 2)
        
        grad_scores = self.attn_weights * (grad_attn_weights - np.sum(self.attn_weights * grad_attn_weights, axis=-1, keepdims=True))
        grad_scores = grad_scores / np.sqrt(self.d_k)
        
        grad_Q = grad_scores @ self.K
        grad_K = grad_scores.transpose(0, 1, 3, 2) @ self.Q
        
        grad_Q = grad_Q.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        grad_K = grad_K.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        grad_V = grad_V.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        self.grad_W_q = self.x.reshape(-1, self.d_model).T @ grad_Q.reshape(-1, self.d_model)
        self.grad_W_k = self.x.reshape(-1, self.d_model).T @ grad_K.reshape(-1, self.d_model)
        self.grad_W_v = self.x.reshape(-1, self.d_model).T @ grad_V.reshape(-1, self.d_model)
        self.grad_W_o = (self.attn_weights @ self.V).transpose(0, 2, 1, 3).reshape(-1, self.d_model).T @ grad_output.reshape(-1, self.d_model)
        
        grad_input = grad_Q @ self.W_q.T + grad_K @ self.W_k.T + grad_V @ self.W_v.T
        return grad_input


class FeedForward:
    def __init__(self, d_model: int, d_ff: int):
        self.d_model = d_model
        self.d_ff = d_ff
        
        self.W1 = np.random.randn(d_model, d_ff) * np.sqrt(2.0 / d_model)
        self.b1 = np.zeros((1, d_ff))
        self.W2 = np.random.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff)
        self.b2 = np.zeros((1, d_model))
        
        self.grad_W1 = np.zeros_like(self.W1)
        self.grad_b1 = np.zeros_like(self.b1)
        self.grad_W2 = np.zeros_like(self.W2)
        self.grad_b2 = np.zeros_like(self.b2)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        self.x = x
        self.z1 = x @ self.W1 + self.b1
        self.a1 = np.maximum(0, self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        return self.z2
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        self.grad_W2 = self.a1.reshape(-1, self.d_ff).T @ grad_output.reshape(-1, self.d_model)
        self.grad_b2 = np.sum(grad_output, axis=(0, 1), keepdims=True)
        
        grad_a1 = grad_output @ self.W2.T
        grad_z1 = grad_a1 * (self.z1 > 0)
        
        self.grad_W1 = self.x.reshape(-1, self.d_model).T @ grad_z1.reshape(-1, self.d_ff)
        self.grad_b1 = np.sum(grad_z1, axis=(0, 1), keepdims=True)
        
        grad_input = grad_z1 @ self.W1.T
        return grad_input


class TransformerBlock:
    def __init__(self, d_model: int, n_heads: int, d_ff: int, max_seq_len: int):
        self.d_model = d_model
        self.attn = MultiHeadAttention(d_model, n_heads, max_seq_len)
        self.ln1 = LayerNorm(d_model)
        self.ff = FeedForward(d_model, d_ff)
        self.ln2 = LayerNorm(d_model)
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        attn_out = self.attn.forward(x, training)
        x = x + attn_out
        x = self.ln1.forward(x)
        
        ff_out = self.ff.forward(x)
        x = x + ff_out
        x = self.ln2.forward(x)
        
        self.residual1 = attn_out
        self.residual2 = ff_out
        self.x_before_ln1 = x - self.residual1
        self.x_before_ln2 = x - self.residual2
        
        return x
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        grad_ln2 = self.ln2.backward(grad_output)
        grad_ff_out = grad_ln2
        grad_x_before_ff = self.ff.backward(grad_ff_out)
        grad_x_before_ln2 = grad_x_before_ff + grad_ln2
        
        grad_ln1 = self.ln1.backward(grad_x_before_ln2)
        grad_attn_out = grad_ln1
        grad_x_before_attn = self.attn.backward(grad_attn_out)
        grad_input = grad_x_before_attn + grad_ln1
        
        return grad_input


class TransformerLM:
    def __init__(self, vocab_size: int, n_layers: int, n_heads: int, d_model: int, d_ff: int, max_seq_len: int):
        self.vocab_size = vocab_size
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.d_model = d_model
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        
        self.token_embedding = np.random.randn(vocab_size, d_model) * np.sqrt(2.0 / d_model)
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * np.sqrt(2.0 / d_model)
        
        self.grad_token_embedding = np.zeros_like(self.token_embedding)
        self.grad_pos_embedding = np.zeros_like(self.pos_embedding)
        
        self.blocks = [TransformerBlock(d_model, n_heads, d_ff, max_seq_len) for _ in range(n_layers)]
        self.ln_final = LayerNorm(d_model)
        self.output_proj = np.random.randn(d_model, vocab_size) * np.sqrt(2.0 / d_model)
        self.grad_output_proj = np.zeros_like(self.output_proj)
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        batch_size, seq_len = x.shape
        
        token_emb = self.token_embedding[x]
        pos_emb = self.pos_embedding[np.arange(seq_len)]
        x_emb = token_emb + pos_emb
        
        self.x = x
        self.x_emb = x_emb
        self.token_emb = token_emb
        self.seq_len = seq_len
        
        x = x_emb
        for block in self.blocks:
            x = block.forward(x, training)
        
        x = self.ln_final.forward(x)
        logits = x @ self.output_proj
        
        self.activations = x
        return logits
    
    def backward(self, grad_logits: np.ndarray) -> None:
        batch_size, seq_len = self.x.shape
        
        self.grad_output_proj = self.activations.reshape(-1, self.d_model).T @ grad_logits.reshape(-1, self.vocab_size)
        grad_x = grad_logits @ self.output_proj.T
        grad_x = self.ln_final.backward(grad_x)
        
        for block in reversed(self.blocks):
            grad_x = block.backward(grad_x)
        
        grad_pos_emb = np.sum(grad_x, axis=0)[:self.seq_len]
        grad_token_emb = np.zeros_like(self.token_embedding)
        
        for b in range(batch_size):
            np.add.at(grad_token_emb, self.x[b], grad_x[b])
        
        self.grad_token_embedding = grad_token_emb
        self.grad_pos_embedding[:self.seq_len] = grad_pos_emb
    
    def parameters(self):
        params = [
            ('token_embedding', self.token_embedding, self.grad_token_embedding),
            ('pos_embedding', self.pos_embedding, self.grad_pos_embedding),
            ('output_proj', self.output_proj, self.grad_output_proj),
        ]
        
        for i, block in enumerate(self.blocks):
            params.append((f'block_{i}_attn_Wq', block.attn.W_q, block.attn.grad_W_q))
            params.append((f'block_{i}_attn_Wk', block.attn.W_k, block.attn.grad_W_k))
            params.append((f'block_{i}_attn_Wv', block.attn.W_v, block.attn.grad_W_v))
            params.append((f'block_{i}_attn_Wo', block.attn.W_o, block.attn.grad_W_o))
            params.append((f'block_{i}_ln1_gamma', block.ln1.gamma, block.ln1.grad_gamma))
            params.append((f'block_{i}_ln1_beta', block.ln1.beta, block.ln1.grad_beta))
            params.append((f'block_{i}_ff_W1', block.ff.W1, block.ff.grad_W1))
            params.append((f'block_{i}_ff_b1', block.ff.b1, block.ff.grad_b1))
            params.append((f'block_{i}_ff_W2', block.ff.W2, block.ff.grad_W2))
            params.append((f'block_{i}_ff_b2', block.ff.b2, block.ff.grad_b2))
            params.append((f'block_{i}_ln2_gamma', block.ln2.gamma, block.ln2.grad_gamma))
            params.append((f'block_{i}_ln2_beta', block.ln2.beta, block.ln2.grad_beta))
        
        params.append(('ln_final_gamma', self.ln_final.gamma, self.ln_final.grad_gamma))
        params.append(('ln_final_beta', self.ln_final.beta, self.ln_final.grad_beta))
        
        return params


def cross_entropy_loss(logits: np.ndarray, targets: np.ndarray) -> Tuple[float, np.ndarray]:
    batch_size, seq_len, vocab_size = logits.shape
    
    logits_stable = logits - np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_stable)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    targets_flat = targets.reshape(-1)
    probs_flat = probs.reshape(-1, vocab_size)
    
    correct_log_probs = -np.log(probs_flat[np.arange(len(targets_flat)), targets_flat] + 1e-12)
    loss = np.mean(correct_log_probs)
    
    grad_logits = probs_flat.copy()
    grad_logits[np.arange(len(targets_flat)), targets_flat] -= 1
    grad_logits = grad_logits.reshape(batch_size, seq_len, vocab_size) / (batch_size * seq_len)
    
    return loss, grad_logits