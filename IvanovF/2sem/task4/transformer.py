import numpy as np
from utils import softmax, gelu, gelu_backward, causal_mask, init_weights


class Embedding:
    def __init__(self, vocab_size: int, d_model: int, max_seq_len: int):
        self.token_emb = init_weights((vocab_size, d_model))
        self.pos_emb = init_weights((max_seq_len, d_model))
        self.cache = {}
        self.grads = {}
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        B, T = x.shape
        tok = self.token_emb[x]
        pos = self.pos_emb[np.arange(T)]
        self.cache = {'x': x, 'tok': tok}
        return tok + pos
    
    def backward(self, grad: np.ndarray) -> dict:
        x = self.cache['x']
        B, T, D = grad.shape
        gt = np.zeros_like(self.token_emb)
        gp = np.zeros_like(self.pos_emb)
        for b in range(B):
            for t in range(T):
                gt[x[b,t]] += grad[b,t]
                gp[t] += grad[b,t]
        self.grads = {'token_emb': gt, 'pos_emb': gp}
        return self.grads
    
    def params(self): return {'token_emb': self.token_emb, 'pos_emb': self.pos_emb}
    def load_params(self, p): self.token_emb, self.pos_emb = p['token_emb'], p['pos_emb']


class LayerNorm:
    def __init__(self, d: int, eps: float = 1e-5):
        self.eps, self.d = eps, d
        self.gamma = np.ones(d, dtype=np.float32)
        self.beta = np.zeros(d, dtype=np.float32)
        self.cache, self.grads = {}, {}
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        mean, var = x.mean(-1, keepdims=True), x.var(-1, keepdims=True)
        xn = (x - mean) / np.sqrt(var + self.eps)
        self.cache = {'x': x, 'xn': xn, 'mean': mean, 'var': var}
        return xn * self.gamma + self.beta
    
    def backward(self, grad: np.ndarray) -> tuple[np.ndarray, dict]:
        x, xn, mean, var = [self.cache[k] for k in ['x','xn','mean','var']]
        N = self.d
        self.grads = {
            'gamma': (grad * xn).sum((0,1)),
            'beta': grad.sum((0,1))
        }
        std_inv = 1. / np.sqrt(var + self.eps)
        dxn = grad * self.gamma
        dvar = (dxn * (x-mean) * -0.5 * std_inv**3).sum((0,1), keepdims=True)
        dmean = (dxn * -std_inv).sum((0,1), keepdims=True)
        dx = dxn * std_inv + dvar * 2*(x-mean)/N + dmean/N
        return dx, self.grads
    
    def params(self): return {'gamma': self.gamma, 'beta': self.beta}
    def load_params(self, p): self.gamma, self.beta = p['gamma'], p['beta']


class MLP:
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.0):
        self.W1 = init_weights((d_model, d_ff))
        self.b1 = np.zeros(d_ff, dtype=np.float32)
        self.W2 = init_weights((d_ff, d_model))
        self.b2 = np.zeros(d_model, dtype=np.float32)
        self.dropout = dropout
        self.cache, self.grads = {}, {}
        
    def forward(self, x: np.ndarray, training: bool = False) -> np.ndarray:
        z1 = x @ self.W1 + self.b1
        h1 = gelu(z1)
        if training and self.dropout > 0:
            mask = (np.random.rand(*h1.shape) > self.dropout).astype(np.float32)
            h1 = h1 * mask / (1 - self.dropout + 1e-9)
            self.cache['mask'] = mask
        self.cache.update({'x': x, 'z1': z1, 'h1': h1})
        return h1 @ self.W2 + self.b2
    
    def backward(self, grad: np.ndarray) -> tuple[np.ndarray, dict]:
        x, z1, h1 = self.cache['x'], self.cache['z1'], self.cache['h1']
        gW2 = h1.reshape(-1, h1.shape[-1]).T @ grad.reshape(-1, grad.shape[-1])
        gb2 = grad.sum((0,1))
        gh1 = grad @ self.W2.T
        if 'mask' in self.cache:
            gh1 = gh1 * self.cache['mask'] / (1 - self.dropout + 1e-9)
        gz1 = gelu_backward(z1, gh1)
        gW1 = x.reshape(-1, x.shape[-1]).T @ gz1.reshape(-1, gz1.shape[-1])
        gb1 = gz1.sum((0,1))
        dx = gz1 @ self.W1.T
        self.grads = {'W1': gW1, 'b1': gb1, 'W2': gW2, 'b2': gb2}
        return dx, self.grads
    
    def params(self): return {'W1': self.W1, 'b1': self.b1, 'W2': self.W2, 'b2': self.b2}
    def load_params(self, p):
        for k in p: setattr(self, k, p[k])


class MultiHeadAttention:
    def __init__(self, d_model: int, n_head: int, dropout: float = 0.0):
        assert d_model % n_head == 0
        self.d_model, self.n_head = d_model, n_head
        self.d_head = d_model // n_head
        self.dropout = dropout
        s = 0.02
        self.W_q = init_weights((n_head, d_model, self.d_head)) * s
        self.W_k = init_weights((n_head, d_model, self.d_head)) * s
        self.W_v = init_weights((n_head, d_model, self.d_head)) * s
        self.W_o = init_weights((d_model, d_model)) * s
        self.cache, self.grads = {}, {}
        
    def forward(self, x: np.ndarray, mask: np.ndarray, training: bool = False) -> np.ndarray:
        B, T, _ = x.shape
        h = self.n_head
        Q = np.einsum('btd,hdc->bhtc', x, self.W_q)
        K = np.einsum('btd,hdc->bhtc', x, self.W_k)
        V = np.einsum('btd,hdc->bhtc', x, self.W_v)
        scores = np.einsum('bhtc,bhsc->bhts', Q, K) / np.sqrt(self.d_head)
        scores = scores + mask
        attn = softmax(scores)
        if training and self.dropout > 0:
            dm = (np.random.rand(*attn.shape) > self.dropout).astype(np.float32)
            attn = attn * dm / (1 - self.dropout + 1e-9)
            self.cache['drop_mask'] = dm
        out = np.einsum('bhts,bhsc->bhtc', attn, V)
        out = out.transpose(0,2,1,3).reshape(B, T, -1)
        pre_o = out
        out = out @ self.W_o
        self.cache.update({'x': x, 'Q': Q, 'K': K, 'V': V, 'attn': attn, 'pre_o': pre_o})
        return out
    
    def backward(self, grad: np.ndarray) -> tuple[np.ndarray, dict]:
        B, T, _ = grad.shape
        h, dh = self.n_head, self.d_head
        x = self.cache['x']
        Q, K, V, attn = [self.cache[k] for k in ['Q','K','V','attn']]
        
        gWo = self.cache['pre_o'].reshape(-1, self.d_model).T @ grad.reshape(-1, self.d_model)
        dx = grad @ self.W_o.T
        gh = dx.reshape(B, T, h, dh).transpose(0,2,1,3)
        
        gV = np.einsum('bhts,bhtc->bhsc', attn, gh)
        gAttn = np.einsum('bhtc,bhsc->bhts', gh, V)
        gScores = attn * (gAttn - np.sum(gAttn * attn, axis=-1, keepdims=True))
        gScores = np.where(self.cache['mask'] == -np.inf, 0, gScores)
        
        gQ = np.einsum('bhts,bhsc->bhtc', gScores, K)
        gK = np.einsum('bhts,bhsc->bhtc', gScores.transpose(0,1,3,2), Q)
        
        gWq = np.einsum('btd,bhtc->hdc', x, gQ)
        gWk = np.einsum('btd,bhtc->hdc', x, gK)
        gWv = np.einsum('btd,bhtc->hdc', x, gV)
        
        dx_q = np.einsum('bhtc,hdc->btd', gQ, self.W_q)
        dx_k = np.einsum('bhtc,hdc->btd', gK, self.W_k)
        dx_v = np.einsum('bhtc,hdc->btd', gV, self.W_v)
        dx = dx_q + dx_k + dx_v
        
        self.grads = {'W_q': gWq, 'W_k': gWk, 'W_v': gWv, 'W_o': gWo}
        return dx, self.grads
    
    def set_mask(self, mask): self.cache['mask'] = mask
    def params(self): return {'W_q': self.W_q, 'W_k': self.W_k, 'W_v': self.W_v, 'W_o': self.W_o}
    def load_params(self, p):
        for k in p: setattr(self, k, p[k])


class TransformerBlock:
    def __init__(self, d_model: int, n_head: int, d_ff: int, dropout: float = 0.1):
        self.attn = MultiHeadAttention(d_model, n_head, dropout)
        self.ln1, self.ln2 = LayerNorm(d_model), LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff, dropout)
        self.grads = {}
        
    def forward(self, x: np.ndarray, mask: np.ndarray, training: bool = False) -> np.ndarray:
        self.attn.set_mask(mask)
        x = x + self.attn.forward(self.ln1.forward(x), mask, training)
        x = x + self.mlp.forward(self.ln2.forward(x), training)
        return x
    
    def backward(self, grad: np.ndarray) -> dict:
        g = grad
        g, g_mlp = self.mlp.backward(g)
        g, g_ln2 = self.ln2.backward(g)
        g = g + grad  # residual
        g, g_attn = self.attn.backward(g)
        g, g_ln1 = self.ln1.backward(g)
        g = g + grad  # residual
        self.grads = {**g_attn, **g_ln1, **g_mlp, **g_ln2}
        return g, self.grads
    
    def params(self):
        p = {}
        for m in [self.attn, self.ln1, self.ln2, self.mlp]: p.update(m.params())
        return p
    def load_params(self, p):
        for m in [self.attn, self.ln1, self.ln2, self.mlp]: m.load_params({k:v for k,v in p.items() if k in m.params()})


class TransformerLM:
    def __init__(self, vocab_size: int, max_seq_len: int, d_model: int = 128, 
                 n_layer: int = 2, n_head: int = 2, d_ff: int = 256, dropout: float = 0.1):
        self.emb = Embedding(vocab_size, d_model, max_seq_len)
        self.blocks = [TransformerBlock(d_model, n_head, d_ff, dropout) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = init_weights((d_model, vocab_size))
        self.d_model, self.vocab_size = d_model, vocab_size
        self.cache, self.grads = {}, {}
        
    def forward(self, x: np.ndarray, training: bool = False) -> np.ndarray:
        B, T = x.shape
        mask = causal_mask(T)
        x = self.emb.forward(x)
        for block in self.blocks:
            x = block.forward(x, mask, training)
        x = self.ln_f.forward(x)
        logits = x @ self.head
        self.cache = {'x': x, 'logits': logits, 'mask': mask}
        return logits
    
    def backward(self, grad_logits: np.ndarray) -> dict:
        g = grad_logits @ self.head.T
        ghead = self.cache['x'].reshape(-1, self.d_model).T @ grad_logits.reshape(-1, self.vocab_size)
        g, g_lnf = self.ln_f.backward(g)
        for block in reversed(self.blocks):
            g, _ = block.backward(g)
        g_emb = self.emb.backward(g)
        self.grads = {**g_emb, 'head': ghead, **g_lnf}
        return self.grads
    
    def params(self):
        p = {'head': self.head}
        p.update(self.emb.params())
        p.update(self.ln_f.params())
        for i, b in enumerate(self.blocks):
            for k, v in b.params().items(): p[f'block{i}_{k}'] = v
        return p
    
    def load_params(self, p):
        if 'head' in p: self.head = p['head']
        self.emb.load_params({k:v for k,v in p.items() if k in ['token_emb','pos_emb']})
        self.ln_f.load_params({k:v for k,v in p.items() if k in ['gamma','beta']})
        for i, b in enumerate(self.blocks):
            prefix = f'block{i}_'
            b.load_params({k.replace(prefix,''):v for k,v in p.items() if k.startswith(prefix)})
    
    def generate(self, prompt: list[int], max_new: int, temperature: float = 1.0, top_k: int = None) -> list[int]:
        ctx = prompt.copy()
        for _ in range(max_new):
            inp = np.array([ctx[-256:]])
            logits = self.forward(inp, training=False)[0, -1] / temperature
            if top_k:
                kth = np.partition(logits, -top_k)[-top_k]
                logits[logits < kth] = -np.inf
            probs = softmax(logits)
            nxt = np.random.choice(len(probs), p=probs)
            ctx.append(int(nxt))
        return ctx