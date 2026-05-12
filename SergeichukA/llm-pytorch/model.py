import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        # Проекции Q, K, V и выход
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)

        # Causal mask buffer (макс. длина 2048, PyTorch сам перенесёт на GPU/CPU)
        self.register_buffer("causal_mask", torch.tril(torch.ones(2048, 2048)).view(1, 1, 2048, 2048))

    def forward(self, x):
        B, T, C = x.size()
        assert C == self.d_model

        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)

        # Разбиваем на головы: (B, T, C) -> (B, n_heads, T, d_head)
        q = q.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        k = k.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.d_head).transpose(1, 2)

        # Scaled dot-product attention
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_head)

        # Применяем causal mask только для текущей длины T
        mask = self.causal_mask[:, :, :T, :T]
        attn_scores = attn_scores.masked_fill(mask == 0, float('-inf'))

        attn_probs = F.softmax(attn_scores, dim=-1)
        attn_probs = self.attn_dropout(attn_probs)

        y = torch.matmul(attn_probs, v)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.out_proj(y)
        return self.resid_dropout(y)


class MLP(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.0):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff, bias=False)
        self.gelu = nn.GELU()
        self.fc2 = nn.Linear(d_ff, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        x = self.fc1(x)
        x = self.gelu(x)
        x = self.fc2(x)
        return self.dropout(x)


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.0):
        super().__init__()
        self.ln_1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_heads, dropout)
        self.ln_2 = nn.LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff, dropout)

    def forward(self, x):
        # Pre-LayerNorm Architecture (стабильнее Post-LN)
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x


class TransformerLM(nn.Module):
    def __init__(self, vocab_size, block_size, d_model=128, n_heads=4, n_layers=2, d_ff=512, dropout=0.1):
        super().__init__()
        self.block_size = block_size

        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.emb_dropout = nn.Dropout(dropout)

        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # Weight Tying: экономит ~30% памяти и параметров
        self.lm_head.weight = self.token_emb.weight

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        device = idx.device
        b, t = idx.size()
        assert t <= self.block_size, f"Sequence length {t} exceeds block_size {self.block_size}"

        pos = torch.arange(0, t, dtype=torch.long, device=device)
        tok_emb = self.token_emb(idx)
        pos_emb = self.pos_emb(pos)
        x = self.emb_dropout(tok_emb + pos_emb)

        for block in self.blocks:
            x = block(x)

        x = self.ln_f(x)

        if targets is not None:
            logits = self.lm_head(x)
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-1)
            return logits, loss
        else:
            # Inference: возвращаем logits только для последнего токена
            logits = self.lm_head(x[:, [-1], :])
            return logits

    def configure_optimizers(self, lr, weight_decay, beta1=0.9, beta2=0.95):
        """
        Разделяет параметры на decay/no-decay для AdamW.
        Bias, LayerNorm и Embeddings НЕ получают weight decay.
        """
        decay = []
        no_decay = []
        for name, param in self.named_parameters():
            if not param.requires_grad:
                continue
            # Веса 2D+ (Linear/Projection) -> weight decay
            # Bias, LayerNorm, Embeddings -> no decay
            if param.dim() <= 1 or name.endswith('.bias') or 'ln_' in name or 'emb' in name:
                no_decay.append(param)
            else:
                decay.append(param)

        optim_groups = [
            {"params": decay, "weight_decay": weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ]
        return torch.optim.AdamW(optim_groups, lr=lr, betas=(beta1, beta2))