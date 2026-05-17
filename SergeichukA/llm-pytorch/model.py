# model.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.register_buffer('mask', torch.tril(torch.ones(1024, 1024)).view(1, 1, 1024, 1024))

    def forward(self, x):
        B, T, C = x.shape
        
        # Проекции и разделение на головы
        Q = self.W_q(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        K = self.W_k(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        V = self.W_v(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = (Q @ K.transpose(-2, -1)) * (1.0 / math.sqrt(self.d_head))
        scores = scores.masked_fill(self.mask[:, :, :T, :T] == 0, float('-inf'))
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        
        # Выход
        out = (attn @ V).transpose(1, 2).contiguous().view(B, T, C)
        return self.W_o(out)

class MLP(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
    
    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_heads, dropout)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff, dropout)
    
    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

class TransformerLM(nn.Module):
    def __init__(self, vocab_size, block_size, d_model=128, n_heads=4, n_layers=2, d_ff=512, dropout=0.0):
        super().__init__()
        self.block_size = block_size
        self.vocab_size = vocab_size
        
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.dropout = nn.Dropout(dropout)
        
        self.blocks = nn.Sequential(*[
            Block(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.token_emb.weight
        
        # Init
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)
    
    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.block_size, f"Input length {T} exceeds block_size {self.block_size}"
        
        # Embeddings
        token_emb = self.token_emb(idx)
        pos_emb = self.pos_emb(torch.arange(T, device=idx.device))
        x = self.dropout(token_emb + pos_emb)
        
        # Transformer blocks
        x = self.blocks(x)
        x = self.ln_f(x)
        
        if targets is not None:
            # Training: возвращаем логиты для всех позиций
            logits = self.lm_head(x)
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)), 
                targets.view(-1), 
                ignore_index=-1
            )
            return logits, loss
        else:
            # Inference: возвращаем логиты только для последнего токена [B, vocab_size]
            logits = self.lm_head(x[:, -1, :])
            return logits
    
    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        """Генерация текста"""
        self.eval()
        for _ in range(max_new_tokens):
            # Обрезаем контекст
            idx_cond = idx if idx.size(1) <= self.block_size else idx[:, -self.block_size:]
            
            # Forward
            logits = self(idx_cond)
            
            # Scaling
            if temperature > 0.0:
                logits = logits / temperature
            
            # Top-k filtering
            if top_k is not None:
                k = min(top_k, logits.size(-1))
                v, _ = torch.topk(logits, k)
                logits[logits < v[:, [-1]]] = -float('inf')
            
            # Sampling
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        
        self.train()
        return idx