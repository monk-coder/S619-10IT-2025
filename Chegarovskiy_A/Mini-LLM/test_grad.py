import numpy as np
import json
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


def numerical_gradient_check(model, x, y, eps=1e-5):
    logits = model.forward(x)
    loss, dlogits = cross_entropy(logits, y)
    model.backward(dlogits)
    params, grads_analytical = model.get_params()

    max_diff = 0
    for i, (p, g) in enumerate(zip(params, grads_analytical)):
        if g is None or p.size == 0:
            continue
        indices = np.random.choice(p.size, min(5, p.size), replace=False)
        for idx in indices:
            original = p.flat[idx]

            p.flat[idx] = original + eps
            loss_plus, _ = cross_entropy(model.forward(x), y)

            p.flat[idx] = original - eps
            loss_minus, _ = cross_entropy(model.forward(x), y)

            p.flat[idx] = original

            grad_numerical = (loss_plus - loss_minus) / (2 * eps)
            grad_analytical = g.flat[idx]

            diff = abs(grad_numerical - grad_analytical) / (abs(grad_numerical) + abs(grad_analytical) + 1e-8)
            max_diff = max(max_diff, diff)

    return max_diff


def main():
    print("=" * 50)
    print("ТЕСТ: падение loss + проверка градиентов")
    print("=" * 50)

    with open('bpe_8000.json', 'r', encoding='utf-8') as f:
        bpe_data = json.load(f)

    vocab = bpe_data['vocab']
    merges = [tuple(m) for m in bpe_data['merges']]
    word_end = bpe_data['word_end']

    text = "мама мыла раму папа мыл раму мама мыла окно"
    tokens = encode_text(text, vocab, merges, word_end)
    data = np.array(tokens * 10)

    seq_len = 32
    batch_size = 4
    epochs = 30

    model = GPT(vocab_size=len(vocab), d_model=64, n_head=2, n_layer=2, d_ff=128, seq_len=seq_len)
    params, _ = model.get_params()
    optim = Adam(params, lr=0.001)

    # Тест градиентов на первом батче
    idx = np.random.randint(0, len(data) - seq_len - 1, batch_size)
    x = np.array([data[i:i + seq_len] for i in idx])
    y = np.array([data[i + 1:i + seq_len + 1] for i in idx])

    max_err = numerical_gradient_check(model, x, y)
    print(f"\nМаксимальная ошибка градиента: {max_err:.2e}")
    if max_err < 1e-4:
        print("✅ Градиенты верны!")
    else:
        print("❌ Ошибка в градиентах!")

    # Проверка падения loss
    print("\n" + "-" * 50)
    losses = []
    for epoch in range(epochs):
        idx = np.random.randint(0, len(data) - seq_len - 1, batch_size)
        x = np.array([data[i:i + seq_len] for i in idx])
        y = np.array([data[i + 1:i + seq_len + 1] for i in idx])

        logits = model.forward(x)
        loss, dlogits = cross_entropy(logits, y)

        model.backward(dlogits)
        _, grads = model.get_params()
        optim.step(grads)

        losses.append(loss)

        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch + 1}/{epochs} | Loss: {loss:.4f}")

    print("-" * 50)
    print(f"Начальный loss: {losses[0]:.4f}")
    print(f"Финальный loss: {losses[-1]:.4f}")

    if losses[-1] < losses[0]:
        print("✅ УСПЕХ! Loss уменьшился — градиенты работают!")
    else:
        print("❌ ОШИБКА! Loss не падает")


if __name__ == '__main__':
    main()