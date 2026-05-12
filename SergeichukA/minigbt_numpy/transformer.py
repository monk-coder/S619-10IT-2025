import numpy as np
from layers import Linear, LayerNorm, Embedding, gelu, gelu_backward
from attention import MultiHeadAttention
from utils import create_causal_mask, cross_entropy_backward

class TransformerBlock:
    def __init__(self, d_model, n_heads, d_ff, dropout=0.0):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_heads, dropout)
        self.ln2 = LayerNorm(d_model)
        self.mlp1 = Linear(d_model, d_ff)
        self.mlp2 = Linear(d_ff, d_model)
        
    def forward(self, x, mask):
        # --- Self-Attention Branch (Pre-LN) ---
        ln1_out = self.ln1.forward(x)
        attn_out = self.attn.forward(ln1_out, mask)
        x2 = x + attn_out  # Residual 1
        
        # --- MLP Branch (Pre-LN) ---
        ln2_out = self.ln2.forward(x2)
        mlp1_pre_act = self.mlp1.forward(ln2_out)
        mlp1_act = gelu(mlp1_pre_act)
        mlp_out = self.mlp2.forward(mlp1_act)
        x_out = x2 + mlp_out  # Residual 2
        
        # Кэшируем только то, что нужно для backward
        self.cache = {'x': x, 'x2': x2, 'mlp1_pre_act': mlp1_pre_act}
        return x_out
    
    def backward(self, grad_output):
        # grad_output имеет размер (B, T, d_model)
        
        # 1. Расщепляем градиент по residual-соединению x_out = x2 + mlp_out
        grad_to_x2 = grad_output
        grad_to_mlp_out = grad_output
        
        # 2. Обратный проход через MLP
        grad_pre_mlp2 = self.mlp2.backward(grad_to_mlp_out)          # (B, T, d_ff)
        grad_post_mlp1 = grad_pre_mlp2 * gelu_backward(self.cache['mlp1_pre_act'])
        grad_pre_mlp1 = self.mlp1.backward(grad_post_mlp1)           # (B, T, d_model)
        grad_from_ln2 = self.ln2.backward(grad_pre_mlp1)             # (B, T, d_model)
        
        # Суммируем градиенты, пришедшие к x2
        total_grad_x2 = grad_to_x2 + grad_from_ln2                   # (B, T, d_model)
        
        # 3. Обратный проход через Attention
        grad_to_attn = total_grad_x2
        grad_to_x1 = total_grad_x2
        
        grad_pre_attn = self.attn.backward(grad_to_attn)             # (B, T, d_model)
        grad_from_ln1 = self.ln1.backward(grad_pre_attn)             # (B, T, d_model)
        
        # Суммируем градиенты, пришедшие к x1 (выход блока)
        return grad_to_x1 + grad_from_ln1
    
    def update(self, lr):
        self.ln1.update(lr)
        self.attn.update(lr)
        self.ln2.update(lr)
        self.mlp1.update(lr)
        self.mlp2.update(lr)


class TransformerLM:
    def __init__(self, vocab_size, max_seq_len, d_model=128, n_heads=4, n_layers=2, d_ff=512, dropout=0.0):
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_seq_len, d_model)
        self.blocks = [TransformerBlock(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)]
        self.ln_f = LayerNorm(d_model)
        self.lm_head = Linear(d_model, vocab_size)
        self.causal_mask = create_causal_mask(max_seq_len)
        self.training = True
        
    def forward(self, x):
        B, T = x.shape
        h = self.token_emb.forward(x) + self.pos_emb.forward(np.arange(T))
        mask = self.causal_mask[:, :, :T, :T]
        for block in self.blocks:
            h = block.forward(h, mask)
        return self.lm_head.forward(self.ln_f.forward(h))
    
    def backward(self, logits, targets):
        h = self.lm_head.backward(cross_entropy_backward(logits, targets, self.vocab_size))
        h = self.ln_f.backward(h)
        for block in reversed(self.blocks):
            h = block.backward(h)
        self.token_emb.backward(h)
        
    def update_params(self, lr):
        self.token_emb.update(lr)
        self.ln_f.update(lr)
        self.lm_head.update(lr)
        for block in self.blocks:
            block.update(lr)