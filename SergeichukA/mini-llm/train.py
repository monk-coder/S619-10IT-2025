import numpy as np
import os
from tokenizer import SimpleBPETokenizer
from model import TransformerLM
import matplotlib.pyplot as plt

# 🔧 МАЛЕНЬКИЕ ПАРАМЕТРЫ ДЛЯ БЫСТРОГО ТЕСТА
BLOCK_SIZE = 32
BATCH_SIZE = 4
MAX_ITERS = 500
LEARNING_RATE = 3e-4
EVAL_INTERVAL = 100
EVAL_ITERS = 5
N_LAYER = 2
N_HEAD = 2
D_MODEL = 64

# Загрузка данных
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters from data.txt")

# Токенизатор
tokenizer = SimpleBPETokenizer(vocab_size=500)
print(f"Training tokenizer with vocab_size={tokenizer.vocab_size}...")
tokenizer.train(text)
tokenizer.save('tokenizer.pkl')
print(f"✓ Tokenizer trained (actual vocab: {len(tokenizer.vocab)})")

data = np.array(tokenizer.encode(text), dtype=np.int32)
print(f"Encoded {len(data)} tokens")

# Проверка размера данных
min_required = BLOCK_SIZE * 4
if len(data) < min_required:
    print(f"⚠ Warning: Data too small ({len(data)} tokens)")
    BLOCK_SIZE = max(8, len(data) // 4)
    print(f"  Adjusted BLOCK_SIZE: {BLOCK_SIZE}")

BATCH_SIZE = max(1, len(data) // (BLOCK_SIZE * 4))
print(f"Final: BLOCK_SIZE={BLOCK_SIZE}, BATCH_SIZE={BATCH_SIZE}")

# Разделение на train/val
val_size = max(BLOCK_SIZE * 2, len(data) // 10)
train_size = len(data) - val_size
train_data = data[:train_size]
val_data = data[train_size:]

vocab_size = len(tokenizer.vocab)
print(f"Vocab size: {vocab_size}")
print(f"Train: {len(train_data)} tokens, Val: {len(val_data)} tokens")

def get_batch(split):
    data = train_data if split == 'train' else val_data
    max_idx = max(1, len(data) - BLOCK_SIZE)
    ix = np.random.randint(0, max_idx, BATCH_SIZE)
    x = np.array([data[i:i+BLOCK_SIZE] for i in ix])
    y = np.array([data[i+1:i+BLOCK_SIZE+1] for i in ix])
    return x, y

def loss_fn(logits, targets):
    B, T, V = logits.shape
    e_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = e_x / e_x.sum(axis=-1, keepdims=True)
    
    loss = 0
    count = 0
    for b in range(B):
        for t in range(T):
            if targets[b, t] < V:
                loss -= np.log(probs[b, t, targets[b, t]] + 1e-9)
                count += 1
    return loss / max(count, 1)

def loss_fn_grad(logits, targets):
    B, T, V = logits.shape
    e_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = e_x / e_x.sum(axis=-1, keepdims=True)
    
    grad = probs.copy()
    for b in range(B):
        for t in range(T):
            if targets[b, t] < V:
                grad[b, t, targets[b, t]] -= 1.0
    return grad / (B * T)

# Модель
print(f"\nInitializing model: d_model={D_MODEL}, n_layer={N_LAYER}, n_head={N_HEAD}")
model = TransformerLM(vocab_size, D_MODEL, N_LAYER, N_HEAD, BLOCK_SIZE)

# 🔧 Оптимизатор Adam (исправленный)
class Adam:
    def __init__(self, model, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.model = model
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        
        # Создаём m и v для каждого параметра
        self.m = {}
        self.v = {}
        
        params = model.get_all_params_with_grads()
        for name, (param, grad) in params.items():
            self.m[name] = np.zeros_like(param)
            self.v[name] = np.zeros_like(param)

    def step(self):
        self.t += 1
        params = self.model.get_all_params_with_grads()
        
        for name, (param, grad) in params.items():
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad ** 2)
            
            m_hat = self.m[name] / (1 - self.beta1 ** self.t)
            v_hat = self.v[name] / (1 - self.beta2 ** self.t)
            
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

optimizer = Adam(model, lr=LEARNING_RATE)

train_losses = []
val_losses = []

def estimate_loss():
    out = {}
    for split in ['train', 'val']:
        losses = np.zeros(EVAL_ITERS)
        for k in range(EVAL_ITERS):
            X, Y = get_batch(split)
            logits = model.forward(X)
            loss = loss_fn(logits, Y)
            losses[k] = loss
        out[split] = losses.mean()
    return out

print("\nStarting training...")
print("=" * 60)

for iter in range(MAX_ITERS):
    if iter % EVAL_INTERVAL == 0 or iter == MAX_ITERS - 1:
        losses = estimate_loss()
        train_losses.append(losses['train'])
        val_losses.append(losses['val'])
        print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    xb, yb = get_batch('train')
    
    logits = model.forward(xb)
    loss = loss_fn(logits, yb)
    
    model.zero_grad()
    dout = loss_fn_grad(logits, yb)
    model.backward(dout)
    
    optimizer.step()

print("=" * 60)
print("Training finished!")

plt.plot(train_losses, label='Train')
plt.plot(np.linspace(0, MAX_ITERS, len(val_losses)), val_losses, label='Val')
plt.legend()
plt.savefig('loss_plot.png')
print("Plot saved to loss_plot.png")

# Сохранение весов
params = model.get_all_params_with_grads()
weights = {name: param for name, (param, grad) in params.items()}
np.savez('model_weights.npz', **weights)
print("Model weights saved to model_weights.npz")
