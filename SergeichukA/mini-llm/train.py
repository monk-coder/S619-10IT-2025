import numpy as np
import time
from tokenizer import SimpleBPETokenizer
from model import TransformerLM
import matplotlib.pyplot as plt

# Hyperparameters
BLOCK_SIZE = 128
BATCH_SIZE = 32
MAX_ITERS = 5000
LEARNING_RATE = 3e-4
EVAL_INTERVAL = 500
EVAL_ITERS = 200
N_LAYER = 4
N_HEAD = 4
D_MODEL = 256

# Device (CPU only for numpy)
device = 'cpu'

# Load Data
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Tokenizer
tokenizer = SimpleBPETokenizer(vocab_size=5000)
# If you have a saved tokenizer from Task 3, load it here. 
# Otherwise train a new one.
if False: # Set to True if you have saved tokenizer
    tokenizer.load('tokenizer.pkl')
else:
    tokenizer.train(text)
    tokenizer.save('tokenizer.pkl')

data = tokenizer.encode(text)
data = np.array(data, dtype=np.int32)
n = int(0.9*len(data))
train_data = data[:n]
val_data = data[n:]

vocab_size = len(tokenizer.vocab)

def get_batch(split):
    data = train_data if split == 'train' else val_data
    ix = np.random.randint(0, len(data) - BLOCK_SIZE, BATCH_SIZE)
    x = np.array([data[i:i+BLOCK_SIZE] for i in ix])
    y = np.array([data[i+1:i+BLOCK_SIZE+1] for i in ix])
    return x, y

@np.vectorize
def cross_entropy_loss(logits, target):
    # logits: (vocab,), target: scalar
    # Softmax + Cross Entropy combined for stability
    e_x = np.exp(logits - np.max(logits))
    probs = e_x / e_x.sum()
    return -np.log(probs[target] + 1e-9)

# However, vectorized is slow. Manual implementation is better.
def loss_fn(logits, targets):
    # logits: (B, T, V), targets: (B, T)
    B, T, V = logits.shape
    # Softmax
    e_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = e_x / e_x.sum(axis=-1, keepdims=True)
    
    # Cross Entropy
    # We need probs[b, t, targets[b, t]]
    loss = 0
    for b in range(B):
        for t in range(T):
            loss -= np.log(probs[b, t, targets[b, t]] + 1e-9)
    return loss / (B * T)

def loss_fn_grad(logits, targets):
    # Gradient of Cross Entropy w.r.t logits is (probs - one_hot)
    B, T, V = logits.shape
    e_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = e_x / e_x.sum(axis=-1, keepdims=True)
    
    grad = probs.copy()
    for b in range(B):
        for t in range(T):
            grad[b, t, targets[b, t]] -= 1.0
    return grad / (B * T)

# Initialize Model
model = TransformerLM(vocab_size, D_MODEL, N_LAYER, N_HEAD, BLOCK_SIZE)

# Optimizer (Adam)
class Adam:
    def __init__(self, model, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.model = model
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = {k: np.zeros_like(v) for k, v in model.parameters().items()}
        self.v = {k: np.zeros_like(v) for k, v in model.parameters().items()}
        # Special handling for embeddings which are not in layer objects
        self.m['token_embedding'] = np.zeros_like(model.token_embedding)
        self.v['token_embedding'] = np.zeros_like(model.token_embedding)
        self.m['pos_embedding'] = np.zeros_like(model.pos_embedding)
        self.v['pos_embedding'] = np.zeros_like(model.pos_embedding)

    def step(self):
        self.t += 1
        params = self.model.parameters()
        
        # Update Embeddings
        for name in ['token_embedding', 'pos_embedding']:
            param = getattr(self.model, name)
            grad = getattr(self.model, f'{name}_grad')
            
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad ** 2)
            
            m_hat = self.m[name] / (1 - self.beta1 ** self.t)
            v_hat = self.v[name] / (1 - self.beta2 ** self.t)
            
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

        # Update Layers
        # Head
        self._update_layer(self.model.head)
        self._update_layer(self.model.ln_f)
        for block in self.model.blocks:
            self._update_layer(block.ln1)
            self._update_layer(block.attn.q_proj)
            self._update_layer(block.attn.k_proj)
            self._update_layer(block.attn.v_proj)
            self._update_layer(block.attn.out_proj)
            self._update_layer(block.ln2)
            self._update_layer(block.mlp.fc1)
            self._update_layer(block.mlp.fc2)

    def _update_layer(self, layer):
        for name, param in layer.parameters().items():
            grad = getattr(layer, f'{name}_grad')
            
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad ** 2)
            
            m_hat = self.m[name] / (1 - self.beta1 ** self.t)
            v_hat = self.v[name] / (1 - self.beta2 ** self.t)
            
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

optimizer = Adam(model, lr=LEARNING_RATE)

# Training Loop
train_losses = []
val_losses = []

@np.vectorize
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

print("Starting training...")
for iter in range(MAX_ITERS):
    if iter % EVAL_INTERVAL == 0 or iter == MAX_ITERS - 1:
        losses = estimate_loss()
        train_losses.append(losses['train'])
        val_losses.append(losses['val'])
        print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    xb, yb = get_batch('train')
    
    # Forward
    logits = model.forward(xb)
    
    # Loss
    loss = loss_fn(logits, yb)
    
    # Backward
    model.zero_grad()
    dout = loss_fn_grad(logits, yb)
    model.backward(dout)
    
    # Update
    optimizer.step()

# Plot
plt.plot(train_losses, label='Train')
plt.plot(np.linspace(0, MAX_ITERS, len(val_losses)), val_losses, label='Val')
plt.legend()
plt.savefig('loss_plot.png')
print("Training finished. Plot saved to loss_plot.png")