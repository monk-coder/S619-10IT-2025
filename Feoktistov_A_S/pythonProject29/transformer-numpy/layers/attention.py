class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        assert d_model % n_head == 0
        self.d_k = d_model // n_head
        self.n_head = n_head
        # Создаем все веса как единые матрицы для эффективности
        self.W_q = np.random.randn(d_model, d_model) * 0.01
        self.W_k = np.random.randn(d_model, d_model) * 0.01
        self.W_v = np.random.randn(d_model, d_model) * 0.01
        self.W_o = np.random.randn(d_model, d_model) * 0.01
        # ... инициализация градиентов

    def forward(self, x, mask=None):
        B, T, D = x.shape
        # 1. Линейные проекции и разделение на головы (heads)
        Q = x @ self.W_q  # (B, T, D)
        K = x @ self.W_k
        V = x @ self.W_v

        # 2. Reshape для голов: (B, T, n_head, d_k) -> (B, n_head, T, d_k)
        Q = Q.reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(B, T, self.n_head, self.d_k).transpose(0, 2, 1, 3)

        # 3. Scaled Dot-Product Attention (с маской!)
        scores = (Q @ K.transpose(0, 1, 3, 2)) / np.sqrt(self.d_k)  # (B, n_head, T, T)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)  # causal mask

        attn_weights = self.softmax(scores, axis=-1)
        context = attn_weights @ V  # (B, n_head, T, d_k)

        # 4. Объединение голов и финальная проекция
        context = context.transpose(0, 2, 1, 3).reshape(B, T, D)
        output = context @ self.W_o
        # Сохраняем промежуточные значения для backward
        # ...
        return output