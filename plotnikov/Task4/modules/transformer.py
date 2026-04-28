import numpy as np
from .embedding import TokenEmbedding, PositionalEmbedding
from .layernorm import LayerNorm
from .attention import MultiHeadCausalAttention
from .mlp import MLP

class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff, max_len=512, seed=42):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadCausalAttention(d_model, n_head, max_len, seed)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff, seed)

    def forward(self, x):
        x = x + self.attn.forward(self.ln1.forward(x))
        x = x + self.mlp.forward(self.ln2.forward(x))
        return x

    def backward(self, grad_output):
        grad_mlp_in = self.ln2.backward(self.mlp.backward(grad_output))
        grad_after_attn = grad_output + grad_mlp_in
        grad_attn_in = self.ln1.backward(self.attn.backward(grad_after_attn))
        return grad_after_attn + grad_attn_in

    def zero_grad(self):
        self.ln1.zero_grad()
        self.attn.zero_grad()
        self.ln2.zero_grad()
        self.mlp.zero_grad()

class TransformerLM:
    def __init__(self, vocab_size, d_model, n_layer, n_head, d_ff, max_len=512, seed=42):
        rng = np.random.default_rng(seed)
        self.token_emb = TokenEmbedding(vocab_size, d_model, seed)
        self.pos_emb = PositionalEmbedding(max_len, d_model, seed + 1)
        self.blocks = [TransformerBlock(d_model, n_head, d_ff, max_len, seed + 2 + i) for i in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.W_out = rng.normal(0, 0.02, (d_model, vocab_size)).astype(np.float32)
        self.grad_W_out = np.zeros_like(self.W_out)
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.max_len = max_len

    def forward(self, x):
        B, T = x.shape
        tok_emb = self.token_emb.forward(x)
        pos_emb = self.pos_emb.forward(T)
        x = tok_emb + pos_emb[None, :, :]
        for block in self.blocks:
            x = block.forward(x)
        x = self.ln_f.forward(x)
        self.x_final = x
        self.T = T
        return x @ self.W_out

    def backward(self, grad_logits):
        x_flat = self.x_final.reshape(-1, self.d_model)
        grad_flat = grad_logits.reshape(-1, self.vocab_size)
        self.grad_W_out += x_flat.T @ grad_flat
        dx = grad_logits @ self.W_out.T
        dx = self.ln_f.backward(dx)
        for block in reversed(self.blocks):
            dx = block.backward(dx)
        self.token_emb.backward(dx)
        self.pos_emb.backward(dx, self.T)
        return dx

    def zero_grad(self):
        self.token_emb.zero_grad()
        self.pos_emb.zero_grad()
        for block in self.blocks:
            block.zero_grad()
        self.ln_f.zero_grad()
        self.grad_W_out.fill(0)

    def get_params(self):
        params = []
        params.append((self.token_emb.weight, self.token_emb.grad, 'token_emb.weight'))
        params.append((self.pos_emb.weight, self.pos_emb.grad, 'pos_emb.weight'))
        for i, block in enumerate(self.blocks):
            prefix = f'blocks.{i}.'
            params.append((block.ln1.gamma, block.ln1.grad_gamma, prefix + 'ln1.gamma'))
            params.append((block.ln1.beta, block.ln1.grad_beta, prefix + 'ln1.beta'))
            params.append((block.attn.W_q, block.attn.grad_W_q, prefix + 'attn.W_q'))
            params.append((block.attn.W_k, block.attn.grad_W_k, prefix + 'attn.W_k'))
            params.append((block.attn.W_v, block.attn.grad_W_v, prefix + 'attn.W_v'))
            params.append((block.attn.W_o, block.attn.grad_W_o, prefix + 'attn.W_o'))
            params.append((block.ln2.gamma, block.ln2.grad_gamma, prefix + 'ln2.gamma'))
            params.append((block.ln2.beta, block.ln2.grad_beta, prefix + 'ln2.beta'))
            params.append((block.mlp.W1, block.mlp.grad_W1, prefix + 'mlp.W1'))
            params.append((block.mlp.b1, block.mlp.grad_b1, prefix + 'mlp.b1'))
            params.append((block.mlp.W2, block.mlp.grad_W2, prefix + 'mlp.W2'))
            params.append((block.mlp.b2, block.mlp.grad_b2, prefix + 'mlp.b2'))
        params.append((self.ln_f.gamma, self.ln_f.grad_gamma, 'ln_f.gamma'))
        params.append((self.ln_f.beta, self.ln_f.grad_beta, 'ln_f.beta'))
        params.append((self.W_out, self.grad_W_out, 'W_out'))
        return params