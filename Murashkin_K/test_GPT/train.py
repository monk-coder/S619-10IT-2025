import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm


from model import TransformerLM, cross_entropy_loss
from optimizer import Adam


print("Подготовка данных и токенизация...")

data_path = "data.txt"
if os.path.exists(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()
else:
    print(f"Предупреждение: Файл {data_path} не найден. Создаем демонстрационный текст...")
    text = "once upon a time in a galaxy far far away, deep learning models were trained on numpy. " * 150

chars = sorted(list(set(text)))
vocab_size = len(chars)

char_to_idx = {ch: i for i, ch in enumerate(chars)}
idx_to_char = {i: ch for i, ch in enumerate(chars)}


data_indices = np.array([char_to_idx[ch] for ch in text], dtype=np.int32)


split_idx = int(0.9 * len(data_indices))
train_data = data_indices[:split_idx]
val_data = data_indices[split_idx:]

print(f"Размер текста: {len(text)} символов. Размер словаря (vocab_size): {vocab_size}")

np.random.seed(42)

T = 64
batch_size = 16
d_model = 128
n_head = 2
n_layer = 2
d_ff = 256
epochs = 5
lr = 5e-4


model = TransformerLM(vocab_size, T, d_model, n_head, n_layer, d_ff)
optimizer = Adam(lr=lr)


def get_batch(data_source, batch_size, context_len):
    ix = np.random.randint(0, len(data_source) - context_len, batch_size)
    x = np.stack([data_source[i: i + context_len] for i in ix])
    y = np.stack([data_source[i + 1: i + context_len + 1] for i in ix])
    return x, y


train_losses = []
val_losses = []


expected_start_loss = -np.log(1.0 / vocab_size)
print(f"Ожидаемый стартовый лосс случайной модели: {expected_start_loss:.4f}\n")
print("Запуск процесса обучения...")

for epoch in range(epochs):
    num_batches = max(10, len(train_data) // (batch_size * T))
    num_batches = min(num_batches, 50)

    epoch_train_loss = 0.0

    for _ in tqdm(range(num_batches), desc=f"Эпоха {epoch + 1}/{epochs}"):
        X, Y = get_batch(train_data, batch_size, T)

        logits = model.forward(X)

        loss, dlogits = cross_entropy_loss(logits, Y)

        model.backward(dlogits)

        optimizer.step(model)

        epoch_train_loss += loss

    X_val, Y_val = get_batch(val_data, batch_size, T)
    val_logits = model.forward(X_val)
    epoch_val_loss, _ = cross_entropy_loss(val_logits, Y_val)

    avg_train_loss = epoch_train_loss / num_batches
    train_losses.append(avg_train_loss)
    val_losses.append(epoch_val_loss)

    print(f"Итог эпохи {epoch + 1:2d}: Train Loss = {avg_train_loss:.4f} | Val Loss = {epoch_val_loss:.4f}")


plt.figure(figsize=(9, 5))
plt.plot(train_losses, label="Train Loss", marker="o")
plt.plot(val_losses, label="Val Loss", marker="s")
plt.xlabel("Эпоха")
plt.ylabel("Кросс-энтропия (Loss)")
plt.title("График сходимости GPT-модели на чистом NumPy")
plt.legend()
plt.grid(True)
plt.savefig("loss_history.png")
print("\nГрафик процесса обучения сохранен в файл 'loss_history.png'")

print("Формирование чекпоинта и сохранение весов...")

checkpoint = {
    "config": {
        "vocab_size": vocab_size,
        "max_len": T,
        "d_model": d_model,
        "n_head": n_head,
        "n_layer": n_layer,
        "d_ff": d_ff
    },
    "weights": {
        "token_emb.weight": model.token_emb.weight,
        "pos_emb.weight": model.pos_emb.weight,
        "lm_head": model.lm_head,
        "ln_f.gamma": model.ln_f.gamma,
        "ln_f.beta": model.ln_f.beta,
        **{f"block_{i}.ln1.gamma": b.ln1.gamma for i, b in enumerate(model.blocks)},
        **{f"block_{i}.ln1.beta": b.ln1.beta for i, b in enumerate(model.blocks)},
        **{f"block_{i}.attn.W_q": b.attn.W_q for i, b in enumerate(model.blocks)},
        **{f"block_{i}.attn.W_k": b.attn.W_k for i, b in enumerate(model.blocks)},
        **{f"block_{i}.attn.W_v": b.attn.W_v for i, b in enumerate(model.blocks)},
        **{f"block_{i}.attn.W_o": b.attn.W_o for i, b in enumerate(model.blocks)},
        **{f"block_{i}.ln2.gamma": b.ln2.gamma for i, b in enumerate(model.blocks)},
        **{f"block_{i}.ln2.beta": b.ln2.beta for i, b in enumerate(model.blocks)},
        **{f"block_{i}.mlp.W1": b.mlp.W1 for i, b in enumerate(model.blocks)},
        **{f"block_{i}.mlp.b1": b.mlp.b1 for i, b in enumerate(model.blocks)},
        **{f"block_{i}.mlp.W2": b.mlp.W2 for i, b in enumerate(model.blocks)},
        **{f"block_{i}.mlp.b2": b.mlp.b2 for i, b in enumerate(model.blocks)},
    },
    "char_to_idx": char_to_idx,
    "idx_to_char": idx_to_char
}

with open("model_weights.pkl", "wb") as f:
    pickle.dump(checkpoint, f)

print("Успех! Файл 'model_weights.pkl' успешно перезаписан и готов для генерации.")

