import numpy as np
import json
import pickle
import argparse
from collections import defaultdict


# ============= BPE Tokenizer =============
class BPETokenizer:
    def __init__(self, vocab_size=300):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.inverse_vocab = {}

    def train(self, text):
        text = text[:30000]
        chars = sorted(list(set(text)))
        self.vocab = {i: char for i, char in enumerate(chars)}
        self.inverse_vocab = {char: i for i, char in enumerate(chars)}

    def encode(self, text):
        return [self.inverse_vocab.get(char, 0) for char in text]

    def decode(self, ids):
        return ''.join([self.vocab.get(id, '') for id in ids])

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'vocab': self.vocab, 'vocab_size': self.vocab_size}, f)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.vocab = {int(k): v for k, v in data['vocab'].items()}
            self.inverse_vocab = {v: int(k) for k, v in self.vocab.items()}
            self.vocab_size = data['vocab_size']


# ============= Utilities =============
def softmax(x, axis=-1):
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / (np.sum(exp_x, axis=axis, keepdims=True) + 1e-10)


def cross_entropy_loss(logits, targets):
    batch_size, seq_len, vocab_size = logits.shape
    probs = softmax(logits.reshape(-1, vocab_size))
    probs = probs.reshape(batch_size, seq_len, vocab_size)

    loss = -np.mean(np.log(probs[np.arange(batch_size)[:, None],
    np.arange(seq_len),
    targets] + 1e-10))

    grad_logits = probs.copy()
    grad_logits[np.arange(batch_size)[:, None], np.arange(seq_len), targets] -= 1
    grad_logits /= (batch_size * seq_len)

    return loss, grad_logits


# ============= Simple Language Model =============
class SimpleLM:
    def __init__(self, vocab_size, d_model, max_len):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_len = max_len

        # Embeddings
        self.token_embed = np.random.randn(vocab_size, d_model) * 0.01
        self.pos_embed = np.random.randn(max_len, d_model) * 0.01

        # Simple feed-forward
        self.W1 = np.random.randn(d_model, d_model) * 0.01
        self.b1 = np.zeros(d_model)
        self.W2 = np.random.randn(d_model, vocab_size) * 0.01
        self.b2 = np.zeros(vocab_size)

        # Gradients
        self.grads = {k: np.zeros_like(v) for k, v in self.get_params().items()}

    def get_params(self):
        return {
            'token_embed': self.token_embed,
            'pos_embed': self.pos_embed,
            'W1': self.W1,
            'b1': self.b1,
            'W2': self.W2,
            'b2': self.b2
        }

    def forward(self, x):
        self.batch_size, self.seq_len = x.shape
        self.x = x

        # Embeddings
        h = self.token_embed[x] + self.pos_embed[:self.seq_len]
        self.h = h

        # Simple transformation
        h1 = np.tanh(h @ self.W1 + self.b1)
        self.h1 = h1
        logits = h1 @ self.W2 + self.b2

        return logits

    def backward(self, grad_logits):
        batch_size, seq_len, vocab_size = grad_logits.shape

        # Gradient for W2 and b2
        self.grads['W2'] += self.h1.reshape(-1, self.d_model).T @ grad_logits.reshape(-1, vocab_size)
        self.grads['b2'] += grad_logits.reshape(-1, vocab_size).sum(axis=0)

        # Gradient for h1
        grad_h1 = grad_logits @ self.W2.T
        grad_h1 = grad_h1 * (1 - self.h1 ** 2)  # derivative of tanh

        # Gradient for W1 and b1
        self.grads['W1'] += self.h.reshape(-1, self.d_model).T @ grad_h1.reshape(-1, self.d_model)
        self.grads['b1'] += grad_h1.reshape(-1, self.d_model).sum(axis=0)

        # Gradient for h
        grad_h = grad_h1 @ self.W1.T

        # Gradient for embeddings
        np.add.at(self.grads['token_embed'], self.x, grad_h)
        self.grads['pos_embed'][:seq_len] += grad_h.sum(axis=0)

    def zero_grad(self):
        for key in self.grads:
            self.grads[key].fill(0)


# ============= SGD Optimizer =============
class SGD:
    def __init__(self, params_dict, lr=1e-3, momentum=0.9):
        self.params = params_dict
        self.lr = lr
        self.momentum = momentum
        self.velocity = {k: np.zeros_like(v) for k, v in params_dict.items()}

    def step(self, grads):
        for name in self.params:
            grad = np.clip(grads[name], -5.0, 5.0)
            self.velocity[name] = self.momentum * self.velocity[name] - self.lr * grad
            self.params[name] += self.velocity[name]


# ============= Training =============
def create_batches(data, batch_size, seq_len):
    data = np.array(data)
    num_batches = (len(data) - 1) // (batch_size * seq_len)
    if num_batches == 0:
        batch_size = 1
        num_batches = (len(data) - 1) // seq_len

    data = data[:num_batches * batch_size * seq_len + 1]

    x = data[:-1].reshape(batch_size, -1)
    y = data[1:].reshape(batch_size, -1)

    x_batches, y_batches = [], []
    for i in range(0, x.shape[1] - seq_len + 1, seq_len):
        x_batches.append(x[:, i:i + seq_len])
        y_batches.append(y[:, i:i + seq_len])

    return x_batches, y_batches


def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=0.8):
    tokens = tokenizer.encode(prompt)

    for _ in range(max_new_tokens):
        if len(tokens) > model.max_len:
            context = tokens[-model.max_len:]
        else:
            context = [0] * (model.max_len - len(tokens)) + tokens

        x = np.array([context])
        logits = model.forward(x)
        probs = softmax(logits[0, -1, :] / temperature)
        probs = np.nan_to_num(probs, nan=0.0)
        probs = probs / probs.sum()
        next_token = np.random.choice(len(probs), p=probs)
        tokens.append(next_token)

    return tokenizer.decode(tokens)


def train(args):
    print("=" * 60)
    print("Simple Language Model")
    print("=" * 60)

    # Загрузка данных
    print(f"\nЗагрузка данных из {args.data_file}...")
    with open(args.data_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:500]  # Меньше данных для стабильности
        text = ' '.join(lines)

    print(f"Загружено {len(text)} символов")

    # Токенизация
    print("\nОбучение токенизатора...")
    tokenizer = BPETokenizer(vocab_size=args.vocab_size)
    tokenizer.train(text)
    print(f"Размер словаря: {len(tokenizer.vocab)} токенов")
    tokenizer.save('tokenizer.json')

    # Кодирование
    print("\nКодирование текста...")
    data = tokenizer.encode(text[:50000])
    print(f"Получено {len(data)} токенов")

    # Train/val split
    split_idx = int(len(data) * 0.9)
    train_data = np.array(data[:split_idx])
    val_data = np.array(data[split_idx:])

    train_x, train_y = create_batches(train_data, args.batch_size, args.seq_len)
    val_x, val_y = create_batches(val_data, args.batch_size, args.seq_len)

    print(f"Train батчей: {len(train_x)}, Val батчей: {len(val_x)}")

    if len(train_x) == 0:
        print("Ошибка: недостаточно данных для обучения. Увеличьте объем текста.")
        return

    # Создание модели
    print("\nСоздание модели...")
    model = SimpleLM(
        vocab_size=args.vocab_size,
        d_model=args.d_model,
        max_len=args.seq_len
    )

    total_params = sum(p.size for p in model.get_params().values())
    print(f"Всего параметров: {total_params:,}")

    optimizer = SGD(model.get_params(), lr=args.lr, momentum=0.9)

    # Обучение
    print("\n" + "=" * 60)
    print("Начало обучения")
    print("=" * 60)

    train_losses = []

    for epoch in range(args.epochs):
        epoch_loss = 0
        for i in range(len(train_x)):
            x_batch = np.array(train_x[i])
            y_batch = np.array(train_y[i])

            logits = model.forward(x_batch)
            loss, grad_logits = cross_entropy_loss(logits, y_batch)

            if np.isnan(loss):
                print(f"\nWarning: NaN loss detected. Stopping training.")
                break

            epoch_loss += loss

            model.zero_grad()
            model.backward(grad_logits)
            optimizer.step(model.grads)

            if i % 10 == 0:
                print(f"Epoch {epoch + 1}/{args.epochs} | Batch {i}/{len(train_x)} | Loss: {loss:.4f}", end='\r')

        if np.isnan(loss):
            break

        avg_train_loss = epoch_loss / len(train_x)
        train_losses.append(avg_train_loss)

        # Validation
        val_loss = 0
        for i in range(min(len(val_x), 10)):
            x_batch = np.array(val_x[i])
            y_batch = np.array(val_y[i])
            logits = model.forward(x_batch)
            loss, _ = cross_entropy_loss(logits, y_batch)
            val_loss += loss

        avg_val_loss = val_loss / min(len(val_x), 10)
        print(f"\nEpoch {epoch + 1}/{args.epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

    # Сохранение модели
    print("\nСохранение модели...")
    with open('model_final.pkl', 'wb') as f:
        pickle.dump(model, f)

    with open('losses.txt', 'w') as f:
        for epoch, loss in enumerate(train_losses):
            f.write(f"Epoch {epoch + 1}: {loss:.4f}\n")

    # Генерация
    print("\n" + "=" * 60)
    print("Примеры генерации:")
    print("=" * 60)

    prompts = ["The", "I", "We"]
    for prompt in prompts:
        generated = generate(model, tokenizer, prompt, max_new_tokens=30, temperature=0.8)
        print(f"\nPrompt: {prompt}")
        print(f"Generated: {generated[:200]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, default='data.txt')
    parser.add_argument('--vocab_size', type=int, default=200)
    parser.add_argument('--d_model', type=int, default=32)
    parser.add_argument('--seq_len', type=int, default=16)
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--lr', type=float, default=0.01)

    args = parser.parse_args()
    train(args)