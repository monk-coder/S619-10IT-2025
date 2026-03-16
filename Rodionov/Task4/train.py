import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
import os
from model import TransformerLM
from bpe_tokenizer import BPETokenizer
from datetime import datetime


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


def create_directories():
    """Создает необходимые директории"""
    dirs = ['checkpoints', 'plots', 'models']
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Created directory: {dir_name}")
    return dirs


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


def compute_accuracy(logits, targets):
    """
    Вычисляет accuracy для батча
    """
    predictions = np.argmax(logits, axis=-1)
    correct = (predictions == targets).sum()
    total = targets.size
    return correct / total


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

    # Эмбеддинги (пока не обучаем)
    grads.append(np.zeros_like(model.token_embedding))
    grads.append(np.zeros_like(model.pos_embedding))

    # Градиенты из блоков
    for block in model.blocks:
        # LayerNorm градиенты
        grads.append(block.ln1.dgamma)
        grads.append(block.ln1.dbeta)
        grads.append(block.ln2.dgamma)
        grads.append(block.ln2.dbeta)

        # Attention градиенты
        grads.append(block.attn.W_q.dW)
        grads.append(block.attn.W_q.db)
        grads.append(block.attn.W_k.dW)
        grads.append(block.attn.W_k.db)
        grads.append(block.attn.W_v.dW)
        grads.append(block.attn.W_v.db)
        grads.append(block.attn.W_o.dW)
        grads.append(block.attn.W_o.db)

        # MLP градиенты
        grads.append(block.mlp.fc1.dW)
        grads.append(block.mlp.fc1.db)
        grads.append(block.mlp.fc2.dW)
        grads.append(block.mlp.fc2.db)

    # Финальные градиенты
    grads.append(model.ln_final.dgamma)
    grads.append(model.ln_final.dbeta)
    grads.append(model.fc_out.dW)
    grads.append(model.fc_out.db)

    return grads


def plot_training_curves(train_losses, val_losses, train_accuracies, val_accuracies, save_path='plots'):
    """Строит и сохраняет графики обучения"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # График loss
    ax1.plot(train_losses, label='Train Loss', marker='o', linewidth=2)
    ax1.plot(val_losses, label='Validation Loss', marker='s', linewidth=2)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # График accuracy
    ax2.plot(train_accuracies, label='Train Accuracy', marker='o', linewidth=2)
    ax2.plot(val_accuracies, label='Validation Accuracy', marker='s', linewidth=2)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Training and Validation Accuracy')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Сохраняем с timestamp
    plot_filename = os.path.join(save_path, f'training_curves_{timestamp}.png')
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {plot_filename}")

    # Также сохраняем как latest для удобства
    latest_filename = os.path.join(save_path, 'training_curves_latest.png')
    plt.savefig(latest_filename, dpi=150, bbox_inches='tight')

    plt.show()


def save_checkpoint(model, optimizer, epoch, train_losses, val_losses, train_accuracies, val_accuracies,
                    save_path='checkpoints'):
    """Сохраняет чекпоинт модели в указанную папку"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    checkpoint = {
        'epoch': epoch,
        'model_state': [p.copy() for p in model.parameters()],
        'optimizer_state': {
            'm': [m.copy() for m in optimizer.m],
            'v': [v.copy() for v in optimizer.v],
            't': optimizer.t
        },
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accuracies': train_accuracies,
        'val_accuracies': val_accuracies,
        'timestamp': timestamp
    }

    # Сохраняем с номером эпохи
    checkpoint_filename = os.path.join(save_path, f'checkpoint_epoch_{epoch + 1:02d}_{timestamp}.pkl')
    with open(checkpoint_filename, 'wb') as f:
        pickle.dump(checkpoint, f)

    # Также сохраняем как latest для удобства
    latest_filename = os.path.join(save_path, 'checkpoint_latest.pkl')
    with open(latest_filename, 'wb') as f:
        pickle.dump(checkpoint, f)

    print(f"Checkpoint saved to {checkpoint_filename}")


def save_final_model(model, tokenizer, metrics, save_path='models'):
    """Сохраняет финальную модель и метрики"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Сохраняем параметры модели
    params = model.parameters()
    param_dict = {f'param_{i}': p for i, p in enumerate(params)}
    model_filename = os.path.join(save_path, f'model_params_{timestamp}.npz')
    np.savez(model_filename, **param_dict)

    # Также сохраняем как latest
    latest_model_filename = os.path.join(save_path, 'model_params_latest.npz')
    np.savez(latest_model_filename, **param_dict)

    # Сохраняем токенизатор
    tokenizer_filename = os.path.join(save_path, f'tokenizer_{timestamp}.pkl')
    with open(tokenizer_filename, 'wb') as f:
        pickle.dump(tokenizer, f)

    # Сохраняем метрики
    metrics_filename = os.path.join(save_path, f'metrics_{timestamp}.pkl')
    with open(metrics_filename, 'wb') as f:
        pickle.dump(metrics, f)

    print(f"Model saved to {model_filename}")
    print(f"Tokenizer saved to {tokenizer_filename}")
    print(f"Metrics saved to {metrics_filename}")


def train(model, tokenizer, data, val_data, epochs=5, batch_size=32, seq_len=128, lr=1e-3):
    # Создаем директории
    dirs = create_directories()
    checkpoint_dir, plots_dir, models_dir = dirs

    optimizer = AdamOptimizer(model.parameters(), lr=lr)

    train_losses = []
    val_losses = []
    train_accuracies = []
    val_accuracies = []
    best_val_accuracy = 0

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        epoch_accuracy = 0
        num_batches = max(1, len(data) // (batch_size * seq_len))

        pbar = tqdm(range(num_batches), desc=f'Epoch {epoch + 1}/{epochs}')
        for batch in pbar:
            # Получаем батч
            x, y = get_batch(data, batch_size, seq_len)

            # Forward pass
            logits = model.forward(x)
            loss, dlogits = cross_entropy_loss(logits, y)

            # Вычисляем accuracy для батча
            accuracy = compute_accuracy(logits, y)

            # Backward pass
            grads = compute_gradients(model, dlogits)

            # Обновление параметров
            optimizer.step(grads)

            epoch_loss += loss
            epoch_accuracy += accuracy
            pbar.set_postfix({
                'loss': f'{loss:.4f}',
                'acc': f'{accuracy:.4f}'
            })

        avg_train_loss = epoch_loss / num_batches
        avg_train_accuracy = epoch_accuracy / num_batches
        train_losses.append(avg_train_loss)
        train_accuracies.append(avg_train_accuracy)

        # Валидация
        model.eval()
        val_loss = 0
        val_accuracy = 0
        num_val_batches = max(1, len(val_data) // (batch_size * seq_len))
        num_val_batches = min(10, num_val_batches)

        for _ in range(num_val_batches):
            x, y = get_batch(val_data, batch_size, seq_len)
            logits = model.forward(x)
            loss, _ = cross_entropy_loss(logits, y)
            accuracy = compute_accuracy(logits, y)
            val_loss += loss
            val_accuracy += accuracy

        avg_val_loss = val_loss / num_val_batches
        avg_val_accuracy = val_accuracy / num_val_batches
        val_losses.append(avg_val_loss)
        val_accuracies.append(avg_val_accuracy)

        print(f'Epoch {epoch + 1}:')
        print(f'  Train - Loss: {avg_train_loss:.4f}, Accuracy: {avg_train_accuracy:.4f}')
        print(f'  Val   - Loss: {avg_val_loss:.4f}, Accuracy: {avg_val_accuracy:.4f}')
        print('-' * 50)

        # Сохраняем чекпоинт после каждой эпохи
        save_checkpoint(model, optimizer, epoch, train_losses, val_losses,
                        train_accuracies, val_accuracies, checkpoint_dir)

        # Сохраняем лучшую модель по validation accuracy
        if avg_val_accuracy > best_val_accuracy:
            best_val_accuracy = avg_val_accuracy
            print(f"New best model! Validation accuracy: {best_val_accuracy:.4f}")

            # Сохраняем лучшую модель
            best_model_path = os.path.join(models_dir, 'best_model.npz')
            params = model.parameters()
            param_dict = {f'param_{i}': p for i, p in enumerate(params)}
            np.savez(best_model_path, **param_dict)

    # Строим и сохраняем графики
    plot_training_curves(train_losses, val_losses, train_accuracies, val_accuracies, plots_dir)

    # Сохраняем финальную модель
    metrics = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accuracies': train_accuracies,
        'val_accuracies': val_accuracies,
        'best_val_accuracy': best_val_accuracy,
        'epochs': epochs,
        'batch_size': batch_size,
        'seq_len': seq_len,
        'lr': lr
    }
    save_final_model(model, tokenizer, metrics, models_dir)

    return train_losses, val_losses, train_accuracies, val_accuracies


def main():
    # Создаем базовые директории
    create_directories()

    # Проверка наличия файла с данными
    #'../../0/data.txt'
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
    train_losses, val_losses, train_accuracies, val_accuracies = train(
        model, tokenizer, train_data, val_data,
        epochs=10,
        batch_size=16,
        seq_len=32,
        lr=3e-2
    )

    print("Training completed!")
    print(f"Final Train Accuracy: {train_accuracies[-1]:.4f}")
    print(f"Final Validation Accuracy: {val_accuracies[-1]:.4f}")
    print(f"\nAll files saved in respective directories:")
    print("  - checkpoints/ - training checkpoints")
    print("  - plots/ - training curves")
    print("  - models/ - final models and tokenizers")


if __name__ == '__main__':

    main()
