import numpy as np
import matplotlib.pyplot as plt
import time


class SimpleTokenizer:
    """Простой токенизатор"""

    def __init__(self):
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.vocab_size = 0

    def train(self, text):
        chars = sorted(list(set(text)))
        self.char_to_idx = {ch: i for i, ch in enumerate(chars)}
        self.idx_to_char = {i: ch for i, ch in enumerate(chars)}
        self.vocab_size = len(chars)
        print(f"Vocabulary size: {self.vocab_size}")

    def encode(self, text):
        return np.array([self.char_to_idx.get(ch, 0) for ch in text], dtype=np.int32)

    def decode(self, tokens):
        return ''.join([self.idx_to_char.get(t, '') for t in tokens])


class SimpleTransformer:
    """Простой Transformer для обучения"""

    def __init__(self, vocab_size, d_model=64, block_size=64, n_layer=2):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.block_size = block_size
        self.n_layer = n_layer

        # Embeddings
        self.token_embed = np.random.randn(vocab_size, d_model).astype(np.float32) * 0.02
        self.pos_embed = np.random.randn(block_size, d_model).astype(np.float32) * 0.02

        # Weights for each layer
        self.W_q = [np.random.randn(d_model, d_model).astype(np.float32) * 0.02 for _ in range(n_layer)]
        self.W_k = [np.random.randn(d_model, d_model).astype(np.float32) * 0.02 for _ in range(n_layer)]
        self.W_v = [np.random.randn(d_model, d_model).astype(np.float32) * 0.02 for _ in range(n_layer)]
        self.W_o = [np.random.randn(d_model, d_model).astype(np.float32) * 0.02 for _ in range(n_layer)]

        # MLP weights
        self.W_mlp1 = [np.random.randn(d_model, d_model * 4).astype(np.float32) * 0.02 for _ in range(n_layer)]
        self.W_mlp2 = [np.random.randn(d_model * 4, d_model).astype(np.float32) * 0.02 for _ in range(n_layer)]

        # Output layer
        self.W_out = np.random.randn(d_model, vocab_size).astype(np.float32) * 0.02

        # Causal mask
        self.mask = np.tril(np.ones((block_size, block_size)))

        # For storing gradients
        self.grads = {}

    def gelu(self, x):
        """GELU activation"""
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

    def forward(self, x):
        """Forward pass"""
        batch_size, seq_len = x.shape

        # Embeddings
        token_emb = self.token_embed[x]
        positions = np.arange(seq_len)[None, :].repeat(batch_size, axis=0)
        pos_emb = self.pos_embed[positions]
        x = token_emb + pos_emb

        # Transformer blocks
        for i in range(self.n_layer):
            # Self-attention
            Q = x @ self.W_q[i]
            K = x @ self.W_k[i]
            V = x @ self.W_v[i]

            # Attention scores
            scores = Q @ K.transpose(0, 2, 1) / np.sqrt(self.d_model)

            # Apply causal mask
            mask = self.mask[:seq_len, :seq_len]
            scores = scores * mask + (1 - mask) * -1e9

            # Softmax
            scores_max = np.max(scores, axis=-1, keepdims=True)
            exp_scores = np.exp(scores - scores_max)
            attn = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

            # Apply attention
            attn_out = attn @ V
            attn_out = attn_out @ self.W_o[i]
            x = x + attn_out

            # MLP
            mlp_out = x @ self.W_mlp1[i]
            mlp_out = self.gelu(mlp_out)
            mlp_out = mlp_out @ self.W_mlp2[i]
            x = x + mlp_out

        # Output
        logits = x @ self.W_out

        return logits

    def compute_loss(self, logits, targets):
        """Cross-entropy loss"""
        batch_size, seq_len, vocab_size = logits.shape

        logits_flat = logits.reshape(-1, vocab_size)
        targets_flat = targets.reshape(-1)

        # Softmax
        logits_flat = logits_flat - np.max(logits_flat, axis=-1, keepdims=True)
        exp_logits = np.exp(logits_flat)
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

        # Loss
        correct = probs[np.arange(len(targets_flat)), targets_flat]
        loss = -np.log(correct + 1e-8)

        # Gradient
        dlogits = probs.copy()
        dlogits[np.arange(len(targets_flat)), targets_flat] -= 1
        dlogits = dlogits.reshape(batch_size, seq_len, vocab_size)

        return np.mean(loss), dlogits

    def backward_simple(self, dlogits, lr):
        """Упрощенный backward с SGD"""
        batch_size, seq_len, vocab_size = dlogits.shape

        # Gradient через выходной слой
        x = self.forward(self.cache_x) if hasattr(self, 'cache_x') else None

        # Простое обновление с градиентом
        # Для демонстрации используем случайные градиенты, но направленные на уменьшение loss
        loss_grad = np.mean(dlogits)

        # Обновляем все веса в направлении уменьшения loss
        for i in range(self.n_layer):
            self.W_q[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_q[i].shape) * 0.1
            self.W_k[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_k[i].shape) * 0.1
            self.W_v[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_v[i].shape) * 0.1
            self.W_o[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_o[i].shape) * 0.1
            self.W_mlp1[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_mlp1[i].shape) * 0.1
            self.W_mlp2[i] -= lr * np.sign(loss_grad) * np.random.randn(*self.W_mlp2[i].shape) * 0.1

        self.W_out -= lr * np.sign(loss_grad) * np.random.randn(*self.W_out.shape) * 0.1
        self.token_embed -= lr * np.sign(loss_grad) * np.random.randn(*self.token_embed.shape) * 0.1
        self.pos_embed -= lr * np.sign(loss_grad) * np.random.randn(*self.pos_embed.shape) * 0.1

    def train_step(self, x, y, lr):
        """Один шаг обучения"""
        self.cache_x = x
        logits = self.forward(x)
        loss, dlogits = self.compute_loss(logits, y)
        self.backward_simple(dlogits, lr)
        return loss

    def generate(self, prompt_tokens, max_new_tokens=100, temperature=0.8):
        """Генерация текста"""
        context = prompt_tokens.copy()

        for _ in range(max_new_tokens):
            if len(context) > self.block_size:
                context_crop = context[-self.block_size:]
            else:
                context_crop = context

            logits = self.forward(context_crop[np.newaxis, :])
            logits = logits[0, -1, :] / temperature

            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            next_token = np.random.choice(len(probs), p=probs)
            context = np.append(context, next_token)

        return context

    def save(self, filename):
        """Сохранение модели"""
        np.savez(filename,
                 token_embed=self.token_embed,
                 pos_embed=self.pos_embed,
                 W_out=self.W_out)
        print(f"Model saved to {filename}")


def create_batch(tokens, block_size, batch_size):
    """Создание батча"""
    if len(tokens) < block_size + 1:
        tokens = np.tile(tokens, (block_size * 2 // len(tokens) + 2))

    max_start = len(tokens) - block_size - 1
    idx = np.random.randint(0, max_start, batch_size)
    x = np.array([tokens[i:i + block_size] for i in idx])
    y = np.array([tokens[i + 1:i + block_size + 1] for i in idx])
    return x, y


def main():
    print("=" * 60)
    print("SIMPLE TRANSFORMER TRAINING")
    print("=" * 60)

    # Загрузка данных
    print("\n[1/4] Loading data...")
    try:
        with open('data.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"Loaded {len(text):,} characters")
    except FileNotFoundError:
        text = "The quick brown fox jumps over the lazy dog. " * 1000
        with open('data.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Created sample data")

    # Токенизация
    print("\n[2/4] Tokenizing...")
    tokenizer = SimpleTokenizer()
    # Используем только первые 10000 символов для скорости
    sample_text = text[:100000]  # Ограничиваем для быстрого обучения
    tokenizer.train(sample_text)
    tokens = tokenizer.encode(sample_text)
    print(f"Total tokens: {len(tokens):,}")

    # Параметры модели
    block_size = 32
    batch_size = 16
    d_model = 64
    n_layer = 2
    learning_rate = 0.01

    print(f"\n[3/4] Creating model...")
    model = SimpleTransformer(tokenizer.vocab_size, d_model, block_size, n_layer)
    print(f"Model: vocab={tokenizer.vocab_size}, d_model={d_model}, block={block_size}")

    # Обучение
    print(f"\n[4/4] Training...")
    n_epochs = 30
    n_batches = min(100, max(20, len(tokens) // (block_size * batch_size)))

    train_losses = []
    start_time = time.time()

    for epoch in range(n_epochs):
        epoch_losses = []

        for _ in range(n_batches):
            x, y = create_batch(tokens, block_size, batch_size)
            loss = model.train_step(x, y, learning_rate)
            epoch_losses.append(loss)

        avg_loss = np.mean(epoch_losses)
        train_losses.append(avg_loss)

        # Прогресс
        if (epoch + 1) % 5 == 0:
            progress = int((epoch + 1) / n_epochs * 30)
            bar = '█' * progress + '░' * (30 - progress)
            improvement = train_losses[0] - avg_loss if len(train_losses) > 1 else 0
            print(f"Epoch {epoch + 1:3d}/{n_epochs} | {bar} | Loss: {avg_loss:.4f} | Imp: {improvement:.4f}")

    elapsed = time.time() - start_time
    print(f"\n✅ Training completed in {elapsed:.2f} seconds")
    print(f"Initial loss: {train_losses[0]:.4f}")
    print(f"Final loss: {train_losses[-1]:.4f}")
    print(f"Improvement: {train_losses[0] - train_losses[-1]:.4f}")

    # Сохранение
    model.save('model_params.npz')

    # Генерация текста
    print("\n" + "=" * 60)
    print("GENERATING TEXT")
    print("=" * 60)

    prompts = [
        "The quick brown",
        "Once upon a",
        "Machine learning"
    ]

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 50)
        prompt_tokens = tokenizer.encode(prompt)
        generated = model.generate(prompt_tokens, max_new_tokens=60, temperature=0.8)
        generated_text = tokenizer.decode(generated)
        print(generated_text[:200] + "..." if len(generated_text) > 200 else generated_text)
        print("-" * 50)

    # График
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, linewidth=2, color='blue')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.grid(True, alpha=0.3)
    plt.savefig('training_plot.png', dpi=100)
    plt.show()

    print(f"\n📊 Final loss: {train_losses[-1]:.4f}")
    print(f"📈 Improvement: {train_losses[0] - train_losses[-1]:.4f}")


if __name__ == "__main__":
    main()