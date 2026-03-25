import json
import numpy as np
import matplotlib.pyplot as plt
from model import GPT, Adam, softmax


def encode_text(text, vocab, merges, word_end):
    tokens = []
    words = text.split()
    for word in words:
        chars = list(word) + [word_end]
        tokens.extend(chars)
    for a, b in merges:
        new_token = a + b
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return [vocab.get(t, 0) for t in tokens]


def cross_entropy(logits, targets):
    B, T, C = logits.shape
    logits_flat = logits.reshape(-1, C)
    targets_flat = targets.reshape(-1)
    probs = softmax(logits_flat, axis=-1)
    loss = -np.mean(np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-9))
    dlogits = probs.copy()
    dlogits[np.arange(len(targets_flat)), targets_flat] -= 1
    dlogits = dlogits / len(targets_flat)
    return loss, dlogits.reshape(B, T, C)


def get_batch(data, seq_len, batch_size):
    idx = np.random.randint(0, len(data) - seq_len - 1, batch_size)
    x = np.array([data[i:i + seq_len] for i in idx])
    y = np.array([data[i + 1:i + seq_len + 1] for i in idx])
    return x, y


def main():
    print("=" * 60)
    print("MINI-LLM: DECODER-ONLY TRANSFORMER")
    print("=" * 60)

    with open('bpe_8000.json', 'r', encoding='utf-8') as f:
        bpe_data = json.load(f)

    vocab = bpe_data['vocab']
    merges = [tuple(m) for m in bpe_data['merges']]
    word_end = bpe_data['word_end']

    print(f"Словарь: {len(vocab)} токенов")

    try:
        with open('data.txt', 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print("Ошибка: data.txt не найден")
        return
    encoded = encode_text(text, vocab, merges, word_end)

    # Искусственно увеличиваем данные для демонстрации обучения
    data = np.array(encoded)

    if len(data) < 33:
        print("Ошибка: текст слишком короткий")
        return

    # Разбиваем на train/val
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    val_data = data[split_idx:]

    seq_len = 32
    batch_size = 16
    steps = 50000

    model = GPT(
        vocab_size=len(vocab), d_model=128, n_head=4, n_layer=2, d_ff=256, seq_len=seq_len
    )

    params, _ = model.get_params()
    optim = Adam(params, lr=0.001)

    train_losses = []
    val_losses = []

    print(f"Обучение {steps} шагов...")

    for step in range(steps):
        x, y = get_batch(train_data, seq_len, batch_size)

        logits = model.forward(x)
        loss, dlogits = cross_entropy(logits, y)

        model.backward(dlogits)
        _, grads = model.get_params()
        optim.step(grads)

        train_losses.append(loss)

        if (step + 1) % 15 == 0:
            x_val, y_val = get_batch(val_data, seq_len, batch_size)
            val_loss, _ = cross_entropy(model.forward(x_val), y_val)
            val_losses.append(val_loss)
            print(f"Шаг {step + 1}/{steps} | Train Loss: {loss:.4f} | Val Loss: {val_loss:.4f}")

    plt.plot(train_losses, label='Train')
    plt.plot(range(14, steps, 15), val_losses, label='Validation', marker='o')
    plt.xlabel('Шаги')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training and Validation Loss')
    plt.savefig('loss.png')

    all_params, _ = model.get_params()
    np.save('model_weights.npy', np.array(all_params, dtype=object))

    print("\nГотово! loss.png и model_weights.npy сохранены.")


if __name__ == '__main__':
    main()