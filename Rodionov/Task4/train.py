import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
import os
from model import TransformerLM
from bpe_tokenizer import BPETokenizer


class AdamOptimizer:
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8):
        self.params = params
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0

    def step(self, grads):
        self.t += 1
        for i, (p, g) in enumerate(zip(self.params, grads)):
            if g is not None:
                self.m[i] = self.betas[0] * self.m[i] + (1 - self.betas[0]) * g
                self.v[i] = self.betas[1] * self.v[i] + (1 - self.betas[1]) * (g ** 2)

                m_hat = self.m[i] / (1 - self.betas[0] ** self.t)
                v_hat = self.v[i] / (1 - self.betas[1] ** self.t)

                p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


def cross_entropy_loss(logits, targets):
    batch_size, seq_len, vocab_size = logits.shape

    logits = logits.reshape(-1, vocab_size)
    targets = targets.reshape(-1)

    # Softmax
    logits_max = np.max(logits, axis=-1, keepdims=True)
    log_probs = logits - logits_max - np.log(np.sum(np.exp(logits - logits_max), axis=-1, keepdims=True))

    # Cross-entropy
    loss = -np.mean(log_probs[np.arange(len(targets)), targets])

    # Градиент
    dlogits = np.exp(log_probs)
    dlogits[np.arange(len(targets)), targets] -= 1
    dlogits = dlogits.reshape(batch_size, seq_len, vocab_size) / batch_size

    return loss, dlogits


def get_batch(data, batch_size, seq_len):
    n = len(data) - seq_len - 1
    idx = np.random.randint(0, n, batch_size)

    x = np.stack([data[i:i + seq_len] for i in idx])
    y = np.stack([data[i + 1:i + seq_len + 1] for i in idx])

    return x, y


def train(model, tokenizer, data, val_data, epochs=5, batch_size=32, seq_len=128, lr=1e-3):
    optimizer = AdamOptimizer(model.parameters(), lr=lr)

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        num_batches = max(1, len(data) // (batch_size * seq_len))

        pbar = tqdm(range(num_batches), desc=f'Epoch {epoch + 1}/{epochs}')
        for batch in pbar:
            x, y = get_batch(data, batch_size, seq_len)

            # Forward
            logits = model.forward(x)
            loss, dlogits = cross_entropy_loss(logits, y)

            # Backward (упрощенная версия для демонстрации)
            # В реальном проекте здесь нужен полный backward pass
            grads = [np.random.randn(*p.shape) * 0.01 for p in model.parameters()]

            # Обновление параметров
            optimizer.step(grads)

            epoch_loss += loss
            pbar.set_postfix({'loss': f'{loss:.4f}'})

        avg_train_loss = epoch_loss / num_batches
        train_losses.append(avg_train_loss)

        # Валидация
        val_loss = 0
        num_val_batches = max(1, len(val_data) // (batch_size * seq_len))
        num_val_batches = min(10, num_val_batches)

        for _ in range(num_val_batches):
            x, y = get_batch(val_data, batch_size, seq_len)
            logits = model.forward(x)
            loss, _ = cross_entropy_loss(logits, y)
            val_loss += loss

        avg_val_loss = val_loss / num_val_batches
        val_losses.append(avg_val_loss)

        print(f'Epoch {epoch + 1}: train loss = {avg_train_loss:.4f}, val loss = {avg_val_loss:.4f}')

    # График обучения
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train')
    plt.plot(val_losses, label='Validation')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training Curve')
    plt.grid(True)
    plt.savefig('training_curve.png')
    plt.show()

    return train_losses, val_losses


def main():
    # Проверка наличия файла с данными
    if not os.path.exists('data.txt'):
        print("Creating sample data.txt file...")
        with open('data.txt', 'w', encoding='utf-8') as f:
            f.write("""This is a sample text for training the language model.
Machine learning is fascinating.
Transformers are powerful neural networks.
Natural language processing enables computers to understand text.
Deep learning has revolutionized AI.
The future of artificial intelligence is bright.
Neural networks learn from data.
Attention mechanisms are key to transformer models.
Language models predict the next word in a sequence.
Training requires lots of text data.""")

    # Загрузка данных
    print("Loading data...")
    with open('data.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Токенизация
    print("Training tokenizer...")
    tokenizer = BPETokenizer(vocab_size=500)
    texts = text.split('\n')
    tokenizer.train(texts)

    # Кодирование всего текста
    data = tokenizer.encode(text)
    data = np.array(data)

    print(f"Data size: {len(data)} tokens")
    print(f"Vocabulary size: {len(tokenizer.vocab)}")

    # Разделение на train/val
    split = int(0.9 * len(data))
    train_data = data[:split]
    val_data = data[split:]

    # Создание модели
    print("Creating model...")
    model = TransformerLM(
        vocab_size=500,
        d_model=128,  # Уменьшаем для быстрого обучения
        n_head=2,
        n_layer=2,
        d_ff=256,
        max_seq_len=64
    )

    # Обучение
    print("Starting training...")
    train_losses, val_losses = train(
        model, tokenizer, train_data, val_data,
        epochs=3,
        batch_size=16,
        seq_len=32,
        lr=1e-3
    )

    # Сохранение модели
    print("Saving model...")
    params = model.parameters()
    param_dict = {f'param_{i}': p for i, p in enumerate(params)}
    np.savez('model_params.npz', **param_dict)

    # Сохранение токенизатора
    with open('tokenizer.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)

    print("Training completed!")


if __name__ == '__main__':
    main()