import numpy as np
import pickle
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

from tokenizer import BPETokenizer
from model import TransformerLM
from utils import cross_entropy_loss, compute_accuracy, Adam

def load_data(filepath, tokenizer_path='tokenizer.pkl', vocab_size=500):
    """Загружает или обучает токенизатор и возвращает данные в виде массива индексов."""
    if os.path.exists(tokenizer_path):
        with open(tokenizer_path, 'rb') as f:
            tokenizer = pickle.load(f)
        if len(tokenizer.vocab) != vocab_size:
            print(f"Предупреждение: сохранённый токенизатор имеет размер {len(tokenizer.vocab)}, "
                  f"запрошен {vocab_size}. Используется существующий.")
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        tokenizer = BPETokenizer(vocab_size=vocab_size)
        print("Обучение токенизатора...")
        tokenizer.train(text)
        with open(tokenizer_path, 'wb') as f:
            pickle.dump(tokenizer, f)
        print("Токенизатор сохранён.")

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    data = tokenizer.encode(text)
    return np.array(data), tokenizer

def get_batch(data, batch_size, seq_len, split='train', val_split=0.1):
    n = len(data)
    split_idx = int(n * (1 - val_split))
    if split == 'train':
        start_idx = 0
        end_idx = split_idx
    else:
        start_idx = split_idx
        end_idx = n
    ix = np.random.randint(start_idx, end_idx - seq_len - 1, size=batch_size)
    x = np.stack([data[i:i+seq_len] for i in ix])
    y = np.stack([data[i+1:i+seq_len+1] for i in ix])
    return x, y

def main():
    vocab_size = 500         
    d_model = 128
    n_layer = 2
    n_head = 2
    max_len = 256
    seq_len = 128
    batch_size = 32
    lr = 1e-3
    epochs = 10                 
    log_every = 100

    data, tokenizer = load_data('data.txt', vocab_size=vocab_size)
    print(f'Размер данных: {len(data)} токенов')
    print(f'Размер словаря: {len(tokenizer.vocab)}')

    model = TransformerLM(vocab_size, d_model, n_layer, n_head, max_len)
    params, _ = model.parameters()
    optimizer = Adam(params, lr=lr)

    train_losses = []
    val_losses = []
    val_accs = []               
    steps = []

    step = 0
    for epoch in range(epochs):
        x_val, y_val = get_batch(data, batch_size, seq_len, split='val')
        logits = model.forward(x_val)
        val_loss, _ = cross_entropy_loss(logits, y_val)
        val_acc = compute_accuracy(logits, y_val)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        steps.append(step)

        num_batches = (len(data) // (batch_size * seq_len)) // 10  # примерное число батчей
        pbar = tqdm(range(num_batches), desc=f'Эпоха {epoch+1}/{epochs}')
        for _ in pbar:
            x, y = get_batch(data, batch_size, seq_len, split='train')
            logits = model.forward(x)
            loss, dlogits = cross_entropy_loss(logits, y)

            model.backward(dlogits)
            _, grads = model.parameters()
            optimizer.step(grads)
            model.zero_grad()

            train_losses.append(loss)
            step += 1
            if step % log_every == 0:
                pbar.set_postfix({'loss': f'{loss:.4f}'})

        print(f"Эпоха {epoch+1}: val loss = {val_loss:.4f}, val acc = {val_acc:.4f}")

    params, _ = model.parameters()
    with open('model_params.pkl', 'wb') as f:
        pickle.dump(params, f)
    print("Модель сохранена в model_params.pkl")

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='train')
    val_steps = np.linspace(0, len(train_losses)-1, len(val_losses))
    plt.plot(val_steps, val_losses, label='val')
    plt.xlabel('шаги')
    plt.ylabel('loss')
    plt.legend()
    plt.title('График потерь')

    plt.subplot(1, 2, 2)
    plt.plot(val_accs, label='val accuracy', color='green')
    plt.xlabel('эпоха')
    plt.ylabel('accuracy')
    plt.legend()
    plt.title('Точность на валидации')

    plt.tight_layout()
    plt.savefig('training_plots.png')
    plt.show()
    print("Графики сохранены в training_plots.png")

if __name__ == '__main__':
    main()
