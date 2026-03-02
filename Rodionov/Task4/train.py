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
                # Обновляем моменты
                self.m[i] = self.betas[0] * self.m[i] + (1 - self.betas[0]) * g
                self.v[i] = self.betas[1] * self.v[i] + (1 - self.betas[1]) * (g ** 2)

                # С коррекцией смещения
                m_hat = self.m[i] / (1 - self.betas[0] ** self.t)
                v_hat = self.v[i] / (1 - self.betas[1] ** self.t)

                # Обновляем параметры
                p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


def cross_entropy_loss(logits, targets):
    """
    Вычисляет кросс-энтропию и её градиент
    """
    batch_size, seq_len, vocab_size = logits.shape

    # Изменяем форму для удобства
    logits_flat = logits.reshape(-1, vocab_size)
    targets_flat = targets.reshape(-1)

    # Стабильный softmax
    logits_max = np.max(logits_flat, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_flat - logits_max)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    # Вычисляем loss
    correct_log_probs = -np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-10)
    loss = np.mean(correct_log_probs)

    # Градиент: dL/dlogits = probs - y_true
    dlogits_flat = probs.copy()
    dlogits_flat[np.arange(len(targets_flat)), targets_flat] -= 1
    dlogits_flat = dlogits_flat / batch_size  # Нормируем на batch size

    # Возвращаем в исходную форму
    dlogits = dlogits_flat.reshape(batch_size, seq_len, vocab_size)

    return loss, dlogits


def get_batch(data, batch_size, seq_len):
    """Получает случайный батч из данных"""
    n = len(data) - seq_len - 1
    idx = np.random.randint(0, n, batch_size)

    x = np.stack([data[i:i + seq_len] for i in idx])
    y = np.stack([data[i + 1:i + seq_len + 1] for i in idx])

    return x, y


def compute_gradients(model, dlogits):
    """
    Собирает все градиенты из модели
    """
    # Запускаем backward pass
    model.backward(dlogits)

    # Собираем градиенты из всех параметров
    grads = []

    # Градиенты эмбеддингов (можно добавить позже)
    grads.append(np.zeros_like(model.token_embedding))  # Пока не обновляем
    grads.append(np.zeros_like(model.pos_embedding))  # Пока не обновляем

    # Градиенты из блоков
    for block in model.blocks:
        # LayerNorm градиенты
        grads.append(block.ln1.gamma_grad if hasattr(block.ln1, 'gamma_grad') else np.zeros_like(block.ln1.gamma))
        grads.append(block.ln1.beta_grad if hasattr(block.ln1, 'beta_grad') else np.zeros_like(block.ln1.beta))
        grads.append(block.ln2.gamma_grad if hasattr(block.ln2, 'gamma_grad') else np.zeros_like(block.ln2.gamma))
        grads.append(block.ln2.beta_grad if hasattr(block.ln2, 'beta_grad') else np.zeros_like(block.ln2.beta))

        # Attention градиенты
        grads.append(block.attn.W_q.W_grad if hasattr(block.attn.W_q, 'W_grad') else np.zeros_like(block.attn.W_q.W))
        grads.append(block.attn.W_q.b_grad if hasattr(block.attn.W_q, 'b_grad') else np.zeros_like(block.attn.W_q.b))
        grads.append(block.attn.W_k.W_grad if hasattr(block.attn.W_k, 'W_grad') else np.zeros_like(block.attn.W_k.W))
        grads.append(block.attn.W_k.b_grad if hasattr(block.attn.W_k, 'b_grad') else np.zeros_like(block.attn.W_k.b))
        grads.append(block.attn.W_v.W_grad if hasattr(block.attn.W_v, 'W_grad') else np.zeros_like(block.attn.W_v.W))
        grads.append(block.attn.W_v.b_grad if hasattr(block.attn.W_v, 'b_grad') else np.zeros_like(block.attn.W_v.b))
        grads.append(block.attn.W_o.W_grad if hasattr(block.attn.W_o, 'W_grad') else np.zeros_like(block.attn.W_o.W))
        grads.append(block.attn.W_o.b_grad if hasattr(block.attn.W_o, 'b_grad') else np.zeros_like(block.attn.W_o.b))

        # MLP градиенты
        grads.append(block.mlp.fc1.W_grad if hasattr(block.mlp.fc1, 'W_grad') else np.zeros_like(block.mlp.fc1.W))
        grads.append(block.mlp.fc1.b_grad if hasattr(block.mlp.fc1, 'b_grad') else np.zeros_like(block.mlp.fc1.b))
        grads.append(block.mlp.fc2.W_grad if hasattr(block.mlp.fc2, 'W_grad') else np.zeros_like(block.mlp.fc2.W))
        grads.append(block.mlp.fc2.b_grad if hasattr(block.mlp.fc2, 'b_grad') else np.zeros_like(block.mlp.fc2.b))

    # Финальные градиенты
    grads.append(
        model.ln_final.gamma_grad if hasattr(model.ln_final, 'gamma_grad') else np.zeros_like(model.ln_final.gamma))
    grads.append(
        model.ln_final.beta_grad if hasattr(model.ln_final, 'beta_grad') else np.zeros_like(model.ln_final.beta))
    grads.append(model.fc_out.W_grad if hasattr(model.fc_out, 'W_grad') else np.zeros_like(model.fc_out.W))
    grads.append(model.fc_out.b_grad if hasattr(model.fc_out, 'b_grad') else np.zeros_like(model.fc_out.b))

    return grads


def train(model, tokenizer, data, val_data, epochs=5, batch_size=32, seq_len=128, lr=1e-3):
    optimizer = AdamOptimizer(model.parameters(), lr=lr)

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        num_batches = max(1, len(data) // (batch_size * seq_len))

        pbar = tqdm(range(num_batches), desc=f'Epoch {epoch + 1}/{epochs}')
        for batch in pbar:
            # Получаем батч
            x, y = get_batch(data, batch_size, seq_len)

            # Forward pass
            logits = model.forward(x)
            loss, dlogits = cross_entropy_loss(logits, y)

            # Backward pass
            grads = compute_gradients(model, dlogits)

            # Обновление параметров
            optimizer.step(grads)

            epoch_loss += loss
            pbar.set_postfix({'loss': f'{loss:.4f}'})

        avg_train_loss = epoch_loss / num_batches
        train_losses.append(avg_train_loss)

        # Валидация
        model.eval()
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

        # Сохраняем чекпоинт после каждой эпохи
        save_checkpoint(model, optimizer, epoch, train_losses, val_losses)

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


def save_checkpoint(model, optimizer, epoch, train_losses, val_losses):
    """Сохраняет чекпоинт модели"""
    checkpoint = {
        'epoch': epoch,
        'model_state': [p.copy() for p in model.parameters()],
        'optimizer_state': {
            'm': [m.copy() for m in optimizer.m],
            'v': [v.copy() for v in optimizer.v],
            't': optimizer.t
        },
        'train_losses': train_losses,
        'val_losses': val_losses
    }

    with open(f'checkpoint_epoch_{epoch + 1}.pkl', 'wb') as f:
        pickle.dump(checkpoint, f)


def main():
    # Проверка наличия файла с данными
    data_path = '../../0/data.txt'
    if not os.path.exists(data_path):
        print(f"Creating sample data.txt file at {data_path}...")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
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
    with open(data_path, 'r', encoding='utf-8') as f:
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
        d_model=128,
        n_head=2,
        n_layer=2,
        d_ff=256,
        max_seq_len=64
    )

    # Обучение
    print("Starting training...")
    train_losses, val_losses = train(
        model, tokenizer, train_data, val_data,
        epochs=10,  # Увеличим количество эпох
        batch_size=16,
        seq_len=32,
        lr=1e-3
    )

    # Сохранение финальной модели
    print("Saving final model...")
    params = model.parameters()
    param_dict = {f'param_{i}': p for i, p in enumerate(params)}
    np.savez('model_params.npz', **param_dict)

    # Сохранение токенизатора
    with open('tokenizer.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)

    print("Training completed!")


if __name__ == '__main__':
    main()