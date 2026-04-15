import numpy as np
from utils import softmax, layer_norm, gelu


class Embedding:
    def __init__(self, vocab_size, d_model):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.weight = np.random.randn(vocab_size, d_model) * 0.02
        self.grad = np.zeros_like(self.weight)

    def forward(self, x):
        """x: (batch_size, seq_len)"""
        self.x = x
        return self.weight[x]

    def backward(self, grad_output):
        """grad_output: (batch_size, seq_len, d_model)"""
        np.add.at(self.grad, self.x, grad_output)
        return None


class PositionalEmbedding:
    def __init__(self, max_len, d_model):
        self.max_len = max_len
        self.d_model = d_model
        self.weight = np.random.randn(max_len, d_model) * 0.02
        self.grad = np.zeros_like(self.weight)

    def forward(self, seq_len):
        """Возвращает позиционные эмбеддинги для seq_len позиций"""
        return self.weight[:seq_len]

    def backward(self, grad_output):
        """grad_output: (seq_len, d_model)"""
        seq_len = grad_output.shape[0]
        self.grad[:seq_len] += grad_output


class MultiHeadAttention:
    def __init__(self, d_model, n_head, max_len):
        self.d_model = d_model
        self.n_head = n_head
        self.d_k = d_model // n_head
        self.max_len = max_len

        # Веса для Q, K, V и выходной проекции
        self.W_q = np.random.randn(d_model, d_model) * 0.02
        self.W_k = np.random.randn(d_model, d_model) * 0.02
        self.W_v = np.random.randn(d_model, d_model) * 0.02
        self.W_o = np.random.randn(d_model, d_model) * 0.02

        # Градиенты
        self.grad_W_q = np.zeros_like(self.W_q)
        self.grad_W_k = np.zeros_like(self.W_k)
        self.grad_W_v = np.zeros_like(self.W_v)
        self.grad_W_o = np.zeros_like(self.W_o)

        # Causal mask
        mask = np.tril(np.ones((max_len, max_len)))
        self.mask = mask.reshape(1, 1, max_len, max_len)

    def forward(self, x):
        """
        x: (batch_size, seq_len, d_model)
        """
        self.batch_size, self.seq_len, _ = x.shape
        self.x = x

        # Линейные проекции
        self.Q = x @ self.W_q  # (batch, seq_len, d_model)
        self.K = x @ self.W_k
        self.V = x @ self.W_v

        # Разделяем на головы
        self.Q = self.Q.reshape(self.batch_size, self.seq_len, self.n_head, self.d_k)
        self.K = self.K.reshape(self.batch_size, self.seq_len, self.n_head, self.d_k)
        self.V = self.V.reshape(self.batch_size, self.seq_len, self.n_head, self.d_k)

        # Транспонируем для удобства
        self.Q = self.Q.transpose(0, 2, 1, 3)  # (batch, n_head, seq_len, d_k)
        self.K = self.K.transpose(0, 2, 1, 3)
        self.V = self.V.transpose(0, 2, 1, 3)

        # Scaled dot-product attention
        scores = self.Q @ self.K.transpose(0, 1, 3, 2) / np.sqrt(self.d_k)

        # Применяем causal mask
        scores = scores + (1 - self.mask[:, :, :self.seq_len, :self.seq_len]) * (-1e9)

        # Softmax
        self.attention_weights = softmax(scores, axis=-1)

        # Применяем attention к values
        self.context = self.attention_weights @ self.V

        # Объединяем головы
        self.context = self.context.transpose(0, 2, 1, 3).reshape(
            self.batch_size, self.seq_len, self.d_model
        )

        # Выходная проекция
        output = self.context @ self.W_o

        return output

    def backward(self, grad_output):
        """
        grad_output: (batch_size, seq_len, d_model)
        """
        # Градиент через выходную проекцию
        self.grad_W_o += self.context.transpose(0, 2, 1) @ grad_output.reshape(
            self.batch_size * self.seq_len, self.d_model
        ).reshape(self.batch_size, self.seq_len, self.d_model)
        grad_context = grad_output @ self.W_o.T

        # Разделяем на головы
        grad_context = grad_context.reshape(
            self.batch_size, self.seq_len, self.n_head, self.d_k
        ).transpose(0, 2, 1, 3)

        # Градиент через attention
        grad_V = self.attention_weights.transpose(0, 1, 3, 2) @ grad_context
        grad_attention = grad_context @ self.V.transpose(0, 1, 3, 2)

        # Градиент через softmax
        grad_scores = self.attention_weights * (
                grad_attention - (self.attention_weights * grad_attention).sum(axis=-1, keepdims=True)
        )
        grad_scores = grad_scores / np.sqrt(self.d_k)

        # Градиент через Q, K, V
        grad_Q = grad_scores @ self.K
        grad_K = grad_scores.transpose(0, 1, 3, 2) @ self.Q
        grad_K = grad_K.transpose(0, 1, 3, 2)

        # Возвращаем размерность
        grad_Q = grad_Q.transpose(0, 2, 1, 3).reshape(self.batch_size, self.seq_len, self.d_model)
        grad_K = grad_K.transpose(0, 2, 1, 3).reshape(self.batch_size, self.seq_len, self.d_model)
        grad_V = grad_V.transpose(0, 2, 1, 3).reshape(self.batch_size, self.seq_len, self.d_model)

        # Градиенты через линейные проекции
        self.grad_W_q += self.x.transpose(0, 2, 1) @ grad_Q.reshape(
            self.batch_size * self.seq_len, self.d_model
        ).reshape(self.batch_size, self.seq_len, self.d_model)

        self.grad_W_k += self.x.transpose(0, 2, 1) @ grad_K.reshape(
            self.batch_size * self.seq_len, self.d_model
        ).reshape(self.batch_size, self.seq_len, self.d_model)

        self.grad_W_v += self.x.transpose(0, 2, 1) @ grad_V.reshape(
            self.batch_size * self.seq_len, self.d_model
        ).reshape(self.batch_size, self.seq_len, self.d_model)

        # Градиент по входу
        grad_x = (
                grad_Q @ self.W_q.T +
                grad_K @ self.W_k.T +
                grad_V @ self.W_v.T
        )

        return grad_x


class FeedForward:
    def __init__(self, d_model, d_ff):
        self.d_model = d_model
        self.d_ff = d_ff

        self.W1 = np.random.randn(d_model, d_ff) * 0.02
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * 0.02
        self.b2 = np.zeros(d_model)

        self.grad_W1 = np.zeros_like(self.W1)
        self.grad_b1 = np.zeros_like(self.b1)
        self.grad_W2 = np.zeros_like(self.W2)
        self.grad_b2 = np.zeros_like(self.b2)

    def forward(self, x):
        self.x = x
        self.hidden = x @ self.W1 + self.b1
        self.hidden_activated = gelu(self.hidden)
        output = self.hidden_activated @ self.W2 + self.b2
        return output

    def backward(self, grad_output):
        # Градиент через W2 и b2
        self.grad_W2 += self.hidden_activated.transpose(0, 2, 1) @ grad_output.reshape(
            grad_output.shape[0] * grad_output.shape[1], grad_output.shape[2]
        ).reshape(grad_output.shape)
        self.grad_b2 += grad_output.sum(axis=(0, 1))

        grad_hidden_activated = grad_output @ self.W2.T

        # Градиент через GELU
        cdf = 0.5 * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (self.hidden + 0.044715 * self.hidden ** 3)))
        pdf = np.exp(-0.5 * self.hidden ** 2) / np.sqrt(2 * np.pi)
        grad_hidden = grad_hidden_activated * (cdf + self.hidden * pdf)

        # Градиент через W1 и b1
        self.grad_W1 += self.x.transpose(0, 2, 1) @ grad_hidden.reshape(
            grad_hidden.shape[0] * grad_hidden.shape[1], grad_hidden.shape[2]
        ).reshape(grad_hidden.shape)
        self.grad_b1 += grad_hidden.sum(axis=(0, 1))

        grad_x = grad_hidden @ self.W1.T
        return grad_x


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff, max_len):
        self.d_model = d_model
        self.attention = MultiHeadAttention(d_model, n_head, max_len)
        self.ff = FeedForward(d_model, d_ff)

        # Параметры LayerNorm
        self.gamma1 = np.ones(d_model)
        self.beta1 = np.zeros(d_model)
        self.gamma2 = np.ones(d_model)
        self.beta2 = np.zeros(d_model)

        self.grad_gamma1 = np.zeros_like(self.gamma1)
        self.grad_beta1 = np.zeros_like(self.beta1)
        self.grad_gamma2 = np.zeros_like(self.gamma2)
        self.grad_beta2 = np.zeros_like(self.beta2)

    def forward(self, x):
        # Attention с residual
        self.norm1, self.cache1 = layer_norm(x, self.gamma1, self.beta1)
        self.attn_out = self.attention.forward(self.norm1)
        x = x + self.attn_out

        # FeedForward с residual
        self.norm2, self.cache2 = layer_norm(x, self.gamma2, self.beta2)
        self.ff_out = self.ff.forward(self.norm2)
        output = x + self.ff_out

        return output

    def backward(self, grad_output):
        # Градиент через второй residual
        grad_ff_out = grad_output
        grad_x2 = grad_output

        # Градиент через FeedForward
        grad_norm2 = self.ff.backward(grad_ff_out)

        # Градиент через второй LayerNorm
        grad_x2_layernorm, grad_gamma2, grad_beta2 = self.layer_norm_backward(
            grad_norm2, self.norm2, self.cache2
        )
        self.grad_gamma2 += grad_gamma2
        self.grad_beta2 += grad_beta2
        grad_x2 += grad_x2_layernorm

        # Градиент через первый residual
        grad_attn_out = grad_x2
        grad_x1 = grad_x2

        # Градиент через Attention
        grad_norm1 = self.attention.backward(grad_attn_out)

        # Градиент через первый LayerNorm
        grad_x1_layernorm, grad_gamma1, grad_beta1 = self.layer_norm_backward(
            grad_norm1, self.norm1, self.cache1
        )
        self.grad_gamma1 += grad_gamma1
        self.grad_beta1 += grad_beta1
        grad_x1 += grad_x1_layernorm

        return grad_x1

    def layer_norm_backward(self, grad_output, x, cache):
        mean, var, x_centered, std_inv = cache
        N = x.shape[-1]

        grad_x_centered = grad_output * self.gamma1 if self.gamma1.shape == grad_output.shape[
                                                                            -1:] else grad_output * self.gamma1.reshape(
            1, 1, -1)

        grad_var = (grad_x_centered * x_centered).sum(axis=-1, keepdims=True) * (-0.5 * std_inv ** 3)
        grad_mean = grad_x_centered.sum(axis=-1, keepdims=True) * (-std_inv)

        grad_x = grad_x_centered * std_inv + grad_var * (2 * x_centered / N) + grad_mean / N

        grad_gamma = (grad_output * x_centered * std_inv).sum(axis=(0, 1))
        grad_beta = grad_output.sum(axis=(0, 1))

        return grad_x, grad_gamma, grad_beta


class TransformerLM:
    def __init__(self, vocab_size, d_model, n_layer, n_head, d_ff, max_len):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layer = n_layer
        self.max_len = max_len

        # Embeddings
        self.token_embedding = Embedding(vocab_size, d_model)
        self.pos_embedding = PositionalEmbedding(max_len, d_model)

        # Transformer blocks
        self.blocks = [
            TransformerBlock(d_model, n_head, d_ff, max_len)
            for _ in range(n_layer)
        ]

        # Final layer norm
        self.ln_final_gamma = np.ones(d_model)
        self.ln_final_beta = np.zeros(d_model)
        self.grad_ln_final_gamma = np.zeros_like(self.ln_final_gamma)
        self.grad_ln_final_beta = np.zeros_like(self.ln_final_beta)

        # Output projection
        self.lm_head = np.random.randn(d_model, vocab_size) * 0.02
        self.grad_lm_head = np.zeros_like(self.lm_head)

    def forward(self, x):
        """
        x: (batch_size, seq_len) - индексы токенов
        returns: (batch_size, seq_len, vocab_size) - логиты
        """
        self.batch_size, self.seq_len = x.shape

        # Token embeddings
        token_emb = self.token_embedding.forward(x)

        # Positional embeddings
        pos_emb = self.pos_embedding.forward(self.seq_len)
        self.hidden = token_emb + pos_emb.reshape(1, self.seq_len, self.d_model)

        # Transformer blocks
        for block in self.blocks:
            self.hidden = block.forward(self.hidden)

        # Final layer norm
        self.hidden_norm, self.cache_final = layer_norm(
            self.hidden, self.ln_final_gamma, self.ln_final_beta
        )

        # Output projection
        logits = self.hidden_norm @ self.lm_head

        return logits

    def backward(self, grad_logits):
        """
        grad_logits: (batch_size, seq_len, vocab_size)
        """
        # Градиент через выходную проекцию
        self.grad_lm_head += self.hidden_norm.transpose(0, 2, 1) @ grad_logits.reshape(
            self.batch_size * self.seq_len, self.vocab_size
        ).reshape(self.batch_size, self.seq_len, self.vocab_size)

        grad_hidden_norm = grad_logits @ self.lm_head.T

        # Градиент через финальный LayerNorm
        grad_hidden, grad_gamma, grad_beta = self.layer_norm_backward_final(
            grad_hidden_norm
        )
        self.grad_ln_final_gamma += grad_gamma
        self.grad_ln_final_beta += grad_beta

        # Градиент через transformer блоки (в обратном порядке)
        for block in reversed(self.blocks):
            grad_hidden = block.backward(grad_hidden)

        # Градиент через позиционные эмбеддинги
        self.pos_embedding.backward(grad_hidden.sum(axis=0))

        # Градиент через токенные эмбеддинги
        self.token_embedding.backward(grad_hidden)

    def layer_norm_backward_final(self, grad_output):
        mean, var, x_centered, std_inv = self.cache_final
        N = self.hidden.shape[-1]

        grad_x_centered = grad_output * self.ln_final_gamma

        grad_var = (grad_x_centered * x_centered).sum(axis=-1, keepdims=True) * (-0.5 * std_inv ** 3)
        grad_mean = grad_x_centered.sum(axis=-1, keepdims=True) * (-std_inv)

        grad_x = grad_x_centered * std_inv + grad_var * (2 * x_centered / N) + grad_mean / N

        grad_gamma = (grad_output * x_centered * std_inv).sum(axis=(0, 1))
        grad_beta = grad_output.sum(axis=(0, 1))

        return grad_x, grad_gamma, grad_beta

    def get_parameters(self):
        """Возвращает все обучаемые параметры и их градиенты"""
        params = []

        # Token embedding
        params.append((self.token_embedding.weight, self.token_embedding.grad))

        # Positional embedding
        params.append((self.pos_embedding.weight, self.pos_embedding.grad))

        # Transformer blocks
        for block in self.blocks:
            # Attention
            params.extend([
                (block.attention.W_q, block.attention.grad_W_q),
                (block.attention.W_k, block.attention.grad_W_k),
                (block.attention.W_v, block.attention.grad_W_v),
                (block.attention.W_o, block.attention.grad_W_o),
            ])

            # FeedForward
            params.extend([
                (block.ff.W1, block.ff.grad_W1),
                (block.ff.b1, block.ff.grad_b1),
                (block.ff.W2, block.ff.grad_W2),
                (block.ff.b2, block.ff.grad_b2),
            ])

            # LayerNorm
            params.extend([
                (block.gamma1, block.grad_gamma1),
                (block.beta1, block.grad_beta1),
                (block.gamma2, block.grad_gamma2),
                (block.beta2, block.grad_beta2),
            ])

        # Final LayerNorm
        params.extend([
            (self.ln_final_gamma, self.grad_ln_final_gamma),
            (self.ln_final_beta, self.grad_ln_final_beta),
        ])

        # LM head
        params.append((self.lm_head, self.grad_lm_head))

        return params