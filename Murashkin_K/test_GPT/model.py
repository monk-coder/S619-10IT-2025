import numpy as np
from modules import Embedding, LayerNorm, MultiHeadAttention, MLP


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)

    def forward(self, x):
        x_ln1 = self.ln1.forward(x)
        x = x + self.attn.forward(x_ln1)
        x_ln2 = self.ln2.forward(x)
        x = x + self.mlp.forward(x_ln2)
        return x

    def backward(self, dout):
        dx_mlp = self.mlp.backward(dout)
        dx_ln2 = self.ln2.backward(dx_mlp)
        dout = dout + dx_ln2

        dx_attn = self.attn.backward(dout)
        dx_ln1 = self.ln1.backward(dx_attn)
        dout = dout + dx_ln1
        return dout


class TransformerLM:
    def __init__(self, vocab_size, max_len, d_model, n_head, n_layer, d_ff):
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_len, d_model)

        self.blocks = [TransformerBlock(d_model, n_head, d_ff) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)

        limit = np.sqrt(6.0 / (d_model + vocab_size))
        self.lm_head = np.random.uniform(-limit, limit, (d_model, vocab_size)).astype(np.float32)
        self.dlm_head = None


    def forward(self, idx):
        B, T = idx.shape
        pos = np.arange(T, dtype=np.int32)

        x = self.token_emb.forward(idx) + self.pos_emb.forward(pos)
        for block in self.blocks:
            x = block.forward(x)

        self.x_final = self.ln_f.forward(x)
        logits = self.x_final.dot(self.lm_head)
        return logits

    def backward(self, dlogits):
        B, T, V = dlogits.shape
        dlogits_flat = dlogits.reshape(-1, V)
        x_final_flat = self.x_final.reshape(-1, self.lm_head.shape[0])

        self.dlm_head = x_final_flat.T.dot(dlogits_flat)
        dx = dlogits_flat.dot(self.lm_head.T).reshape(B, T, -1)

        dx = self.ln_f.backward(dx)
        for block in reversed(self.blocks):
            dx = block.backward(dx)

        dx_pos = np.sum(dx, axis=0)
        self.pos_emb.backward(dx_pos)

        self.token_emb.backward(dx)


def cross_entropy_loss(logits, targets):
    B, T, V = logits.shape
    logits_flat = logits.reshape(-1, V)
    targets_flat = targets.reshape(-1)

    max_logits = np.max(logits_flat, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_flat - max_logits)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    loss = -np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-15)
    loss = np.mean(loss)

    dlogits = probs.copy()
    dlogits[np.arange(len(targets_flat)), targets_flat] -= 1.0
    dlogits /= len(targets_flat)

    return loss, dlogits.reshape(B, T, V)
