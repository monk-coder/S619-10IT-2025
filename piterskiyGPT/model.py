import numpy as np
from layers import LayerNorm, Linear, Embedding
from attention import MultiHeadAttention

class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)
        
    def gelu(self, x):
        # GELU активация: x * Φ(x), где Φ - стандартная нормальная CDF
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))
    
    def forward(self, x):
        self.x = x
        self.h = self.fc1.forward(x)
        self.act = self.gelu(self.h)
        return self.fc2.forward(self.act)
    
    def backward(self, dout):
        d_act = self.fc2.backward(dout)
        
        # Градиент через GELU
        # Производная gelu = 0.5 * (1 + tanh(...)) + 0.5 * x * (1 - tanh(...)^2) * (sqrt(2/pi) + 0.13395 * x^2)
        tanh_arg = np.sqrt(2 / np.pi) * (self.h + 0.044715 * self.h**3)
        tanh_out = np.tanh(tanh_arg)
        d_gelu = 0.5 * (1 + tanh_out) + 0.5 * self.h * (1 - tanh_out**2) * (np.sqrt(2 / np.pi) + 0.134145 * self.h**2)
        
        d_h = d_act * d_gelu
        dx = self.fc1.backward(d_h)
        return dx

class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        
    def forward(self, x, mask=None):
        # Pre-norm архитектура (как в современных GPT)
        attn_input = self.ln1.forward(x)
        attn_out = self.attn.forward(attn_input, mask)
        x = x + attn_out  # Residual
        
        mlp_input = self.ln2.forward(x)
        mlp_out = self.mlp.forward(mlp_input)
        x = x + mlp_out  # Residual
        
        self.cache = {
            'x': x - attn_out,  # x до residual attn
            'attn_input': attn_input,
            'attn_out': attn_out,
            'mlp_input': mlp_input,
            'mlp_out': mlp_out
        }
        
        return x
    
    def backward(self, dout):
        x_before_attn = self.cache['x']
        attn_input = self.cache['attn_input']
        attn_out = self.cache['attn_out']
        mlp_input = self.cache['mlp_input']
        mlp_out = self.cache['mlp_out']
        
        # Residual для MLP
        dmlp_out = dout
        d_mlp_input = self.mlp.backward(dmlp_out)
        dx_after_attn = self.ln2.backward(d_mlp_input)
        
        # Residual для Attention
        dx_before_mlp = dout + dx_after_attn
        dattn_out = dx_before_mlp
        
        # Backward через attention
        d_attn_input = self.attn.backward(dattn_out)
        dx_before_attn = self.ln1.backward(d_attn_input)
        
        # Residual для входа
        dx = dx_before_attn + x_before_attn * 0  # Это просто копия x_before_attn, градиент от residual - это +1
        
        return dx

class TransformerLM:
    def __init__(self, vocab_size, d_model, n_head, n_layer, max_seq_len, d_ff=None):
        if d_ff is None:
            d_ff = d_model * 4
            
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        
        # Эмбеддинги
        self.token_embedding = Embedding(vocab_size, d_model)
        self.pos_embedding = Embedding(max_seq_len, d_model)
        
        # Трансформер блоки
        self.layers = []
        for _ in range(n_layer):
            self.layers.append(TransformerBlock(d_model, n_head, d_ff))
        
        # Финальная LayerNorm и выходной слой
        self.ln_final = LayerNorm(d_model)
        self.output = Linear(d_model, vocab_size)
        
        # Для хранения позиций
        self.pos_cache = None
        
    def create_causal_mask(self, seq_len):
        # Создаем маску, чтобы позиция не видела будущее
        mask = np.triu(np.ones((seq_len, seq_len)) * -np.inf, k=1)
        return mask
    
    def forward(self, x):
        # x: (batch, seq_len)
        batch, seq_len = x.shape
        
        # Позиционные индексы
        positions = np.arange(seq_len).reshape(1, -1)
        positions = np.tile(positions, (batch, 1))
        
        # Эмбеддинги
        token_emb = self.token_embedding.forward(x)
        pos_emb = self.pos_embedding.forward(positions)
        h = token_emb + pos_emb
        
        # Causal mask
        mask = self.create_causal_mask(seq_len)
        
        # Проход через блоки
        for layer in self.layers:
            h = layer.forward(h, mask)
        
        # Финальная нормализация и выход
        h = self.ln_final.forward(h)
        logits = self.output.forward(h)
        
        # Сохраняем для backward
        self.cache = {
            'x': x,
            'positions': positions,
            'token_emb': token_emb,
            'pos_emb': pos_emb,
            'h_before_layers': h,
            'logits': logits
        }
        
        return logits
    
    def backward(self, dlogits):
        # dlogits: (batch, seq_len, vocab_size)
        
        # Градиент через выходной слой
        dh = self.output.backward(dlogits)
        
        # Через финальную LayerNorm
        dh = self.ln_final.backward(dh)
        
        # Через слои в обратном порядке
        for layer in reversed(self.layers):
            dh = layer.backward(dh)
        
        # Градиенты эмбеддингов
        d_token_emb = self.token_embedding.backward(dh)
        d_pos_emb = self.pos_embedding.backward(dh)
        
        return None
    
    def get_parameters(self):
        """Собираем все параметры и градиенты для оптимизатора"""
        params = []
        
        # Эмбеддинги
        params.append((self.token_embedding.W, self.token_embedding.dW))
        params.append((self.pos_embedding.W, self.pos_embedding.dW))
        
        # Слои трансформера
        for layer in self.layers:
            # LayerNorm 1
            params.append((layer.ln1.gamma, layer.ln1.dgamma))
            params.append((layer.ln1.beta, layer.ln1.dbeta))
            
            # Attention слои
            params.append((layer.attn.W_q.W, layer.attn.W_q.dW))
            params.append((layer.attn.W_q.b, layer.attn.W_q.db))
            params.append((layer.attn.W_k.W, layer.attn.W_k.dW))
            params.append((layer.attn.W_k.b, layer.attn.W_k.db))
            params.append((layer.attn.W_v.W, layer.attn.W_v.dW))
            params.append((layer.attn.W_v.b, layer.attn.W_v.db))
            params.append((layer.attn.W_o.W, layer.attn.W_o.dW))
            params.append((layer.attn.W_o.b, layer.attn.W_o.db))
            
            # LayerNorm 2
            params.append((layer.ln2.gamma, layer.ln2.dgamma))
            params.append((layer.ln2.beta, layer.ln2.dbeta))
            
            # MLP
            params.append((layer.mlp.fc1.W, layer.mlp.fc1.dW))
            params.append((layer.mlp.fc1.b, layer.mlp.fc1.db))
            params.append((layer.mlp.fc2.W, layer.mlp.fc2.dW))
            params.append((layer.mlp.fc2.b, layer.mlp.fc2.db))
        
        # Финальные слои
        params.append((self.ln_final.gamma, self.ln_final.dgamma))
        params.append((self.ln_final.beta, self.ln_final.dbeta))
        params.append((self.output.W, self.output.dW))
        params.append((self.output.b, self.output.db))
        
        return params

def loss_fn(logits, targets):
    """Cross-entropy loss"""
    batch, seq_len, vocab_size = logits.shape
    
    # Стабильный softmax
    logits_flat = logits.reshape(-1, vocab_size)
    targets_flat = targets.reshape(-1)
    
    # Log-softmax
    logits_max = np.max(logits_flat, axis=-1, keepdims=True)
    logits_shifted = logits_flat - logits_max
    log_probs = logits_shifted - np.log(np.sum(np.exp(logits_shifted), axis=-1, keepdims=True))
    
    # NLL loss
    loss = -np.mean(log_probs[np.arange(len(targets_flat)), targets_flat])
    
    # Градиент
    dlogits_flat = np.exp(log_probs)  # softmax probabilities
    dlogits_flat[np.arange(len(targets_flat)), targets_flat] -= 1
    dlogits_flat = dlogits_flat / (batch * seq_len)
    
    dlogits = dlogits_flat.reshape(batch, seq_len, vocab_size)
    
    return loss, dlogits
