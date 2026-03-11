import numpy as np
from typing import Optional, Tuple, List, Dict
import pickle

class LayerNorm:
    """Layer Normalization"""
    def __init__(self, d_model: int, eps: float = 1e-5):
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.eps = eps
        self.cache = None
        self.dgamma = None
        self.dbeta = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        x: (batch_size, seq_len, d_model)
        """
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        out = self.gamma * x_norm + self.beta
        
        self.cache = (x, x_norm, mean, var)
        return out
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        """
        dout: градиент сверху (batch_size, seq_len, d_model)
        """
        x, x_norm, mean, var = self.cache
        batch_size, seq_len, d_model = x.shape
        
        # Градиенты для обучаемых параметров
        self.dgamma = np.sum(dout * x_norm, axis=(0, 1))
        self.dbeta = np.sum(dout, axis=(0, 1))
        
        # Градиент по x_norm
        dx_norm = dout * self.gamma
        
        # Градиент по var
        dvar = np.sum(dx_norm * (x - mean) * -0.5 * (var + self.eps)**(-1.5), axis=-1, keepdims=True)
        
        # Градиент по mean
        dmean = np.sum(dx_norm * -1/np.sqrt(var + self.eps), axis=-1, keepdims=True) + \
                dvar * np.mean(-2 * (x - mean), axis=-1, keepdims=True)
        
        # Градиент по x
        dx = dx_norm / np.sqrt(var + self.eps) + \
             dvar * 2 * (x - mean) / d_model + \
             dmean / d_model
        
        return dx


class Dropout:
    """Слой Dropout для предотвращения переобучения"""
    def __init__(self, p=0.1):
        self.p = p
        self.mask = None
        self.training = True
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        self.training = training
        if training and self.p > 0:
            self.mask = np.random.binomial(1, 1-self.p, x.shape) / (1-self.p)
            return x * self.mask
        return x
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        if self.training and self.p > 0 and self.mask is not None:
            return dout * self.mask
        return dout


class Embedding:
    """Слой эмбеддингов"""
    def __init__(self, vocab_size: int, d_model: int):
        # Инициализация Xavier/Glorot
        scale = 1.0 / np.sqrt(vocab_size)
        self.W = np.random.uniform(-scale, scale, (vocab_size, d_model))
        self.dW = np.zeros_like(self.W)
        self.cache = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        x: (batch_size, seq_len) - индексы токенов
        returns: (batch_size, seq_len, d_model)
        """
        self.cache = x
        return self.W[x]
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        """
        dout: (batch_size, seq_len, d_model)
        """
        x = self.cache
        batch_size, seq_len = x.shape
        
        # Инициализируем градиент нулями
        self.dW = np.zeros_like(self.W)
        
        # Аккумулируем градиенты для каждого токена (векторизованная версия)
        for b in range(batch_size):
            for s in range(seq_len):
                token_idx = x[b, s]
                self.dW[token_idx] += dout[b, s]
        
        return None


class PositionalEncoding:
    """Синусоидальные позиционные эмбеддинги"""
    def __init__(self, max_seq_len: int, d_model: int):
        self.pe = np.zeros((max_seq_len, d_model))
        
        position = np.arange(0, max_seq_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
        
        self.pe[:, 0::2] = np.sin(position * div_term)
        self.pe[:, 1::2] = np.cos(position * div_term)
        self.pe = self.pe[np.newaxis, :, :]  # (1, max_seq_len, d_model)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        x: (batch_size, seq_len, d_model)
        добавляем позиционные эмбеддинги
        """
        seq_len = x.shape[1]
        return x + self.pe[:, :seq_len, :]
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        # Позиционные эмбеддинги не обучаются
        return dout


class MultiHeadAttention:
    """Multi-Head Self-Attention с causal mask"""
    def __init__(self, d_model: int, n_head: int, dropout: float = 0.1):
        assert d_model % n_head == 0, "d_model должен делиться на n_head"
        
        self.d_model = d_model
        self.n_head = n_head
        self.head_dim = d_model // n_head
        
        # Инициализация весов
        scale = 1.0 / np.sqrt(d_model)
        self.W_q = np.random.uniform(-scale, scale, (d_model, d_model))
        self.W_k = np.random.uniform(-scale, scale, (d_model, d_model))
        self.W_v = np.random.uniform(-scale, scale, (d_model, d_model))
        self.W_o = np.random.uniform(-scale, scale, (d_model, d_model))
        
        # Для градиентов
        self.dW_q = np.zeros_like(self.W_q)
        self.dW_k = np.zeros_like(self.W_k)
        self.dW_v = np.zeros_like(self.W_v)
        self.dW_o = np.zeros_like(self.W_o)
        
        # Dropout для attention весов
        self.dropout = Dropout(dropout)
        self.cache = None
    
    def _create_causal_mask(self, seq_len: int) -> np.ndarray:
        """Создает causal mask (верхний треугольник -inf)"""
        mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
        return mask[np.newaxis, np.newaxis, :, :]  # (1, 1, seq_len, seq_len)
    
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None, training: bool = True) -> np.ndarray:
        """
        x: (batch_size, seq_len, d_model)
        """
        batch_size, seq_len, _ = x.shape
        
        # Линейные проекции
        Q = x @ self.W_q  # (batch, seq, d_model)
        K = x @ self.W_k
        V = x @ self.W_v
        
        # Разделение на головы: (batch, n_head, seq, head_dim)
        Q = Q.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_head, self.head_dim).transpose(0, 2, 1, 3)
        
        # Вычисление attention scores
        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.head_dim)
        
        # Применение causal mask
        if mask is None:
            mask = self._create_causal_mask(seq_len)
        scores = scores + mask[:, :, :seq_len, :seq_len]
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_probs = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
        
        # Dropout на attention весах
        attn_probs = self.dropout.forward(attn_probs, training)
        
        # Применение attention к значениям
        context = attn_probs @ V  # (batch, n_head, seq, head_dim)
        
        # Объединение голов
        context = context.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        # Выходная проекция
        out = context @ self.W_o
        
        # Сохраняем для backward
        self.cache = (x, Q, K, V, attn_probs, scores, mask)
        
        return out
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        """
        dout: (batch_size, seq_len, d_model)
        """
        x, Q, K, V, attn_probs, scores, mask = self.cache
        batch_size, seq_len, _ = x.shape
        
        # Градиент по выходной проекции
        dcontext = dout @ self.W_o.T  # (batch, seq, d_model)
        x_flat = x.reshape(-1, self.d_model)
        dout_flat = dout.reshape(-1, self.d_model)
        self.dW_o = x_flat.T @ dout_flat
        
        # Разделение на головы
        dcontext = dcontext.reshape(batch_size, seq_len, self.n_head, self.head_dim)
        dcontext = dcontext.transpose(0, 2, 1, 3)  # (batch, n_head, seq, head_dim)
        
        # Backward через dropout
        dattn_probs = self.dropout.backward(dcontext @ V.transpose(0, 1, 3, 2))
        
        # Градиенты по V и attn_probs
        dV = attn_probs.transpose(0, 1, 3, 2) @ dcontext  # (batch, n_head, head_dim, seq)
        dV = dV.transpose(0, 1, 3, 2)  # (batch, n_head, seq, head_dim)
        
        # Градиент по attention scores
        dscores = attn_probs * (dattn_probs - np.sum(attn_probs * dattn_probs, axis=-1, keepdims=True))
        
        # Градиенты по Q и K
        dQ = dscores @ K  # (batch, n_head, seq, head_dim)
        dK = dscores.transpose(0, 1, 3, 2) @ Q  # (batch, n_head, head_dim, seq)
        dK = dK.transpose(0, 1, 3, 2)  # (batch, n_head, seq, head_dim)
        
        # Масштабирование
        dQ = dQ / np.sqrt(self.head_dim)
        dK = dK / np.sqrt(self.head_dim)
        
        # Объединение голов
        dQ = dQ.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dK = dK.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        dV = dV.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        # Градиенты по весам проекций
        self.dW_q = x_flat.T @ dQ.reshape(-1, self.d_model)
        self.dW_k = x_flat.T @ dK.reshape(-1, self.d_model)
        self.dW_v = x_flat.T @ dV.reshape(-1, self.d_model)
        
        # Градиент по входу
        dx = (dQ @ self.W_q.T) + (dK @ self.W_k.T) + (dV @ self.W_v.T)
        
        return dx


class MLP:
    """Двухслойный MLP с GELU активацией и dropout"""
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        scale = 1.0 / np.sqrt(d_model)
        self.W1 = np.random.uniform(-scale, scale, (d_model, d_ff))
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.uniform(-scale, scale, (d_ff, d_model))
        self.b2 = np.zeros(d_model)
        
        self.dW1 = np.zeros_like(self.W1)
        self.db1 = np.zeros_like(self.b1)
        self.dW2 = np.zeros_like(self.W2)
        self.db2 = np.zeros_like(self.b2)
        
        self.dropout = Dropout(dropout)
        self.cache = None
    
    def gelu(self, x: np.ndarray) -> np.ndarray:
        """GELU активация"""
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))
    
    def gelu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Производная GELU"""
        tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3))
        return 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out**2) * \
               np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        x: (batch_size, seq_len, d_model)
        """
        # Первый слой
        hidden = x @ self.W1 + self.b1
        hidden_act = self.gelu(hidden)
        hidden_act = self.dropout.forward(hidden_act, training)
        
        # Второй слой
        out = hidden_act @ self.W2 + self.b2
        
        self.cache = (x, hidden, hidden_act)
        return out
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        """
        dout: (batch_size, seq_len, d_model)
        """
        x, hidden, hidden_act = self.cache
        
        # Градиенты по второму слою
        dhidden_act = dout @ self.W2.T
        dhidden_act = self.dropout.backward(dhidden_act)
        
        self.dW2 = hidden_act.reshape(-1, hidden_act.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        self.db2 = np.sum(dout, axis=(0, 1))
        
        # Градиент по активации
        dhidden = dhidden_act * self.gelu_derivative(hidden)
        
        # Градиенты по первому слою
        self.dW1 = x.reshape(-1, x.shape[-1]).T @ dhidden.reshape(-1, dhidden.shape[-1])
        self.db1 = np.sum(dhidden, axis=(0, 1))
        
        # Градиент по входу
        dx = dhidden @ self.W1.T
        
        return dx


class TransformerBlock:
    """Один блок Transformer с dropout"""
    def __init__(self, d_model: int, n_head: int, d_ff: int, dropout: float = 0.1):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head, dropout)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff, dropout)
        self.dropout = Dropout(dropout)
        
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None, training: bool = True) -> np.ndarray:
        # Self-attention с residual connection
        attn_out = self.attn.forward(self.ln1.forward(x), mask, training)
        attn_out = self.dropout.forward(attn_out, training)
        x = x + attn_out
        
        # MLP с residual connection
        mlp_out = self.mlp.forward(self.ln2.forward(x), training)
        mlp_out = self.dropout.forward(mlp_out, training)
        x = x + mlp_out
        
        return x
    
    def backward(self, dout: np.ndarray) -> np.ndarray:
        # Backward для residual + MLP
        dout_mlp = self.mlp.backward(dout)
        dout_mlp = self.dropout.backward(dout_mlp)
        dout_ln2 = self.ln2.backward(dout_mlp)
        dout = dout + dout_ln2
        
        # Backward для residual + attention
        dout_attn = self.attn.backward(dout)
        dout_attn = self.dropout.backward(dout_attn)
        dout_ln1 = self.ln1.backward(dout_attn)
        dout = dout + dout_ln1
        
        return dout


class TransformerLM:
    """Полная модель Transformer Language Model"""
    def __init__(self, vocab_size: int, d_model: int, n_head: int, n_layer: int, 
                 max_seq_len: int, dropout: float = 0.1, d_ff: Optional[int] = None):
        
        if d_ff is None:
            d_ff = 4 * d_model
        
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.dropout = dropout
        
        # Слои
        self.token_embedding = Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(max_seq_len, d_model)
        self.embed_dropout = Dropout(dropout)
        
        self.blocks = []
        for _ in range(n_layer):
            self.blocks.append(TransformerBlock(d_model, n_head, d_ff, dropout))
        
        self.ln_final = LayerNorm(d_model)
        
        # Выходной линейный слой
        scale = 1.0 / np.sqrt(d_model)
        self.W_out = np.random.uniform(-scale, scale, (d_model, vocab_size))
        self.b_out = np.zeros(vocab_size)
        
        self.dW_out = np.zeros_like(self.W_out)
        self.db_out = np.zeros_like(self.b_out)
        
        # Режим обучения
        self.training = True
    
    def train(self):
        """Переключение в режим обучения"""
        self.training = True
    
    def eval(self):
        """Переключение в режим оценки"""
        self.training = False
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        x: (batch_size, seq_len) - индексы токенов
        returns: (batch_size, seq_len, vocab_size) - логиты
        """
        # Эмбеддинги
        x = self.token_embedding.forward(x)  # (batch, seq, d_model)
        x = self.pos_encoding.forward(x)
        x = self.embed_dropout.forward(x, self.training)
        
        # Трансформер блоки
        for block in self.blocks:
            x = block.forward(x, training=self.training)
        
        # Финальная нормализация
        x = self.ln_final.forward(x)
        
        # Выходной слой
        logits = x @ self.W_out + self.b_out
        
        return logits
    
    def backward(self, dlogits: np.ndarray) -> None:
        """
        dlogits: (batch_size, seq_len, vocab_size)
        """
        # Градиенты выходного слоя
        x = self.ln_final.cache[0]  # вход в ln_final
        x_flat = x.reshape(-1, self.d_model)
        dlogits_flat = dlogits.reshape(-1, self.vocab_size)
        
        self.dW_out = x_flat.T @ dlogits_flat
        self.db_out = np.sum(dlogits, axis=(0, 1))
        
        # Градиент через выходной слой
        dout = dlogits @ self.W_out.T
        dout = dout.reshape(x.shape)
        
        # Backward через финальную нормализацию
        dout = self.ln_final.backward(dout)
        
        # Backward через блоки в обратном порядке
        for block in reversed(self.blocks):
            dout = block.backward(dout)
        
        # Backward через позиционные эмбеддинги (не обучаются)
        dout = self.pos_encoding.backward(dout)
        dout = self.embed_dropout.backward(dout)
        
        # Backward через токен эмбеддинги
        self.token_embedding.backward(dout)
    
    def get_parameters(self) -> List[np.ndarray]:
        """Возвращает список всех обучаемых параметров"""
        params = []
        
        # Embedding
        params.append(self.token_embedding.W)
        
        # Блоки трансформера
        for block in self.blocks:
            # Attention
            params.append(block.attn.W_q)
            params.append(block.attn.W_k)
            params.append(block.attn.W_v)
            params.append(block.attn.W_o)
            # MLP
            params.append(block.mlp.W1)
            params.append(block.mlp.b1)
            params.append(block.mlp.W2)
            params.append(block.mlp.b2)
            # LayerNorm
            params.append(block.ln1.gamma)
            params.append(block.ln1.beta)
            params.append(block.ln2.gamma)
            params.append(block.ln2.beta)
        
        # Финальный LayerNorm
        params.append(self.ln_final.gamma)
        params.append(self.ln_final.beta)
        
        # Выходной слой
        params.append(self.W_out)
        params.append(self.b_out)
        
        return params
    
    def get_gradients(self) -> List[np.ndarray]:
        """Возвращает список градиентов для всех параметров"""
        grads = []
        
        # Embedding
        grads.append(self.token_embedding.dW)
        
        # Блоки трансформера
        for block in self.blocks:
            # Attention
            grads.append(block.attn.dW_q)
            grads.append(block.attn.dW_k)
            grads.append(block.attn.dW_v)
            grads.append(block.attn.dW_o)
            # MLP
            grads.append(block.mlp.dW1)
            grads.append(block.mlp.db1)
            grads.append(block.mlp.dW2)
            grads.append(block.mlp.db2)
            # LayerNorm
            grads.append(block.ln1.dgamma)
            grads.append(block.ln1.dbeta)
            grads.append(block.ln2.dgamma)
            grads.append(block.ln2.dbeta)
        
        # Финальный LayerNorm
        grads.append(self.ln_final.dgamma)
        grads.append(self.ln_final.dbeta)
        
        # Выходной слой
        grads.append(self.dW_out)
        grads.append(self.db_out)
        
        return grads
    
    def zero_grad(self):
        """Обнуление градиентов"""
        self.token_embedding.dW.fill(0)
        
        for block in self.blocks:
            block.attn.dW_q.fill(0)
            block.attn.dW_k.fill(0)
            block.attn.dW_v.fill(0)
            block.attn.dW_o.fill(0)
            block.mlp.dW1.fill(0)
            block.mlp.db1.fill(0)
            block.mlp.dW2.fill(0)
            block.mlp.db2.fill(0)
            block.ln1.dgamma = None
            block.ln1.dbeta = None
            block.ln2.dgamma = None
            block.ln2.dbeta = None
        
        self.ln_final.dgamma = None
        self.ln_final.dbeta = None
        self.dW_out.fill(0)
        self.db_out.fill(0)
    
    def save(self, path: str):
        """Сохраняет модель"""
        params = self.get_parameters()
        with open(path, 'wb') as f:
            pickle.dump({
                'params': params,
                'vocab_size': self.vocab_size,
                'd_model': self.d_model,
                'max_seq_len': self.max_seq_len,
                'dropout': self.dropout
            }, f)
    
    def load(self, path: str):
        """Загружает модель"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        # Здесь нужно сопоставить параметры
        params = data['params']
        # ... код для загрузки параметров в слои


def loss_and_accuracy(logits: np.ndarray, targets: np.ndarray) -> Tuple[float, np.ndarray, float]:
    """
    Cross-entropy loss с расчетом accuracy
    logits: (batch_size, seq_len, vocab_size)
    targets: (batch_size, seq_len) - индексы правильных токенов
    returns: loss, dlogits, accuracy
    """
    batch_size, seq_len, vocab_size = logits.shape
    
    # Стабильный softmax
    logits_max = np.max(logits, axis=-1, keepdims=True)
    logits_stable = logits - logits_max
    exp_logits = np.exp(logits_stable)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    # Выбираем вероятности правильных токенов
    probs_target = probs[np.arange(batch_size)[:, np.newaxis], 
                         np.arange(seq_len)[np.newaxis, :], 
                         targets]
    
    # Loss
    loss = -np.mean(np.log(probs_target + 1e-8))
    
    # Расчет accuracy
    predictions = np.argmax(logits, axis=-1)
    correct = (predictions == targets)
    accuracy = np.mean(correct)
    
    # Градиент
    dlogits = probs.copy()
    dlogits[np.arange(batch_size)[:, np.newaxis], 
            np.arange(seq_len)[np.newaxis, :], 
            targets] -= 1
    dlogits = dlogits / (batch_size * seq_len)
    
    return loss, dlogits, accuracy
