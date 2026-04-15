import numpy as np
import argparse
import pickle
import json


# ============= Tokenizer (совместимый с train.py) =============
class BPETokenizer:
    def __init__(self, vocab_size=300):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.inverse_vocab = {}
        self.merges = []  # Для совместимости

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
            json.dump({
                'vocab': self.vocab,
                'vocab_size': self.vocab_size,
                'merges': []  # Пустой список для совместимости
            }, f)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.vocab = {int(k): v for k, v in data['vocab'].items()}
            self.inverse_vocab = {v: int(k) for k, v in self.vocab.items()}
            self.vocab_size = data['vocab_size']
            self.merges = data.get('merges', [])  # Безопасное получение


# ============= Utilities =============
def softmax(x, axis=-1):
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / (np.sum(exp_x, axis=axis, keepdims=True) + 1e-10)


# ============= SimpleLM (такая же как в train.py) =============
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


# ============= Генерация =============
def top_k_sampling(logits, temperature=1.0, top_k=None):
    logits = logits / temperature
    if top_k is not None and top_k > 0:
        indices_to_remove = logits < np.sort(logits)[-top_k]
        logits[indices_to_remove] = -np.inf
    probs = softmax(logits)
    probs = np.nan_to_num(probs, nan=0.0)
    if probs.sum() == 0:
        probs = np.ones_like(probs) / len(probs)
    else:
        probs = probs / probs.sum()
    return np.random.choice(len(probs), p=probs)


def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=1.0, top_k=None):
    tokens = tokenizer.encode(prompt)

    for _ in range(max_new_tokens):
        if len(tokens) > model.max_len:
            context = tokens[-model.max_len:]
        else:
            context = [0] * (model.max_len - len(tokens)) + tokens

        x = np.array([context])
        logits = model.forward(x)
        next_token_logits = logits[0, -1, :]
        next_token = top_k_sampling(next_token_logits, temperature, top_k)
        tokens.append(next_token)

    return tokenizer.decode(tokens)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True, help='Промпт для генерации')
    parser.add_argument('--model', type=str, default='model_final.pkl', help='Путь к модели')
    parser.add_argument('--tokenizer', type=str, default='tokenizer.json', help='Путь к токенизатору')
    parser.add_argument('--max_tokens', type=int, default=100, help='Максимальное число токенов')
    parser.add_argument('--temperature', type=float, default=0.8, help='Температура')
    parser.add_argument('--top_k', type=int, default=50, help='Top-k сэмплирование')

    args = parser.parse_args()

    # Загрузка токенизатора
    print("Загрузка токенизатора...")
    tokenizer = BPETokenizer()
    tokenizer.load(args.tokenizer)
    print(f"Словарь загружен: {len(tokenizer.vocab)} токенов")

    # Загрузка модели
    print("Загрузка модели...")
    with open(args.model, 'rb') as f:
        model = pickle.load(f)
    print("Модель загружена")

    # Генерация
    print(f"\n{'=' * 60}")
    print(f"Промпт: {args.prompt}")
    print('=' * 60)

    generated = generate(
        model, tokenizer, args.prompt,
        max_new_tokens=args.max_tokens,
        temperature=args.temperature,
        top_k=args.top_k
    )

    print(f"\nСгенерированный текст:\n{generated}")
    print('=' * 60)


if __name__ == "__main__":
    main()