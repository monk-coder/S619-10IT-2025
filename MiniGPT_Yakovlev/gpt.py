import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
import urllib.request
import ssl
from collections import deque

import config
from tokenizer import BPETokenizer


def download_file_from_github(url, save_path):
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        print(f"Downloading data from GitHub: {url}")
        urllib.request.urlretrieve(url, save_path)
        print(f"Data saved to {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download from GitHub: {e}")
        return False


def find_data_file():
    if os.path.exists(config.DATA_PATH):
        print(f"Found data file locally: {config.DATA_PATH}")
        return config.DATA_PATH
    
    print(f"Local data file not found: {config.DATA_PATH}")
    
    if hasattr(config, 'GITHUB_DATA_URL') and config.GITHUB_DATA_URL:
        if download_file_from_github(config.GITHUB_DATA_URL, config.DATA_PATH):
            return config.DATA_PATH
    
    search_paths = [
        "data.txt", "./data.txt", "../data.txt", "data/data.txt",
        "dataset/data.txt", "datasets/data.txt"
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            print(f"Found data file at: {path}")
            return path
    
    print("Warning: No data.txt found.")
    return None


def stream_lines(file_path, chunk_size=1000):
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.strip():
                lines.append(line)
                if len(lines) >= chunk_size:
                    yield lines
                    lines = []
    if lines:
        yield lines


def create_chunks_from_lines(lines, tokenizer, seq_len):
    all_ids = []
    for line in lines:
        ids = tokenizer.encode(line)
        ids.append(tokenizer.eos_token_id)
        all_ids.extend(ids)
    
    all_ids = np.array(all_ids)
    X, Y = [], []
    for i in range(0, len(all_ids) - seq_len, seq_len):
        chunk = all_ids[i:i+seq_len+1]
        if len(chunk) == seq_len + 1:
            X.append(chunk[:-1])
            Y.append(chunk[1:])
    
    return np.array(X) if X else np.array([]).reshape(0, seq_len), \
           np.array(Y) if Y else np.array([]).reshape(0, seq_len)


def load_data_chunked(tokenizer, seq_len, chunk_size=1000):
    data_path = find_data_file()
    if data_path is None:
        raise FileNotFoundError("data.txt not found.")
    
    print(f"Loading data in chunks of {chunk_size} lines...")
    
    all_X, all_Y = [], []
    total_lines = 0
    
    for chunk_lines in stream_lines(data_path, chunk_size):
        total_lines += len(chunk_lines)
        X, Y = create_chunks_from_lines(chunk_lines, tokenizer, seq_len)
        if len(X) > 0:
            all_X.append(X)
            all_Y.append(Y)
        print(f"  Processed {total_lines} lines, {sum(len(x) for x in all_X)} samples so far")
    
    if not all_X:
        raise ValueError("No data samples created. Check your data file.")
    
    train_X = np.vstack(all_X)
    train_Y = np.vstack(all_Y)
    
    split = int(len(train_X) * 0.9)
    train_X_final = train_X[:split]
    train_Y_final = train_Y[:split]
    val_X_final = train_X[split:]
    val_Y_final = train_Y[split:]
    
    print(f"Total samples: {len(train_X_final)} train, {len(val_X_final)} val")
    
    return (train_X_final, train_Y_final), (val_X_final, val_Y_final)


def load_data_generator(tokenizer, seq_len, batch_size=32, chunk_size=500):
    data_path = find_data_file()
    if data_path is None:
        raise FileNotFoundError("data.txt not found.")
    
    print(f"Using streaming data loader (batch_size={batch_size})")
    
    buffer_X, buffer_Y = [], []
    
    for chunk_lines in stream_lines(data_path, chunk_size):
        X, Y = create_chunks_from_lines(chunk_lines, tokenizer, seq_len)
        
        for i in range(len(X)):
            buffer_X.append(X[i])
            buffer_Y.append(Y[i])
            
            if len(buffer_X) >= batch_size:
                batch_X = np.array(buffer_X[:batch_size])
                batch_Y = np.array(buffer_Y[:batch_size])
                yield batch_X, batch_Y
                buffer_X = buffer_X[batch_size:]
                buffer_Y = buffer_Y[batch_size:]
        
        X, Y = None, None
    
    if buffer_X:
        yield np.array(buffer_X), np.array(buffer_Y)


def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))


def gelu_backward(x):
    tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3))
    return 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out**2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)


class Embedding:
    def __init__(self, num_embeddings, embedding_dim):
        self.weight = np.random.randn(num_embeddings, embedding_dim) * 0.02
        self.grad = np.zeros_like(self.weight)
    
    def forward(self, x):
        self.x = x
        return self.weight[x]
    
    def backward(self, dout):
        self.grad.fill(0)
        np.add.at(self.grad, self.x, dout)
        return None
    
    def update(self, lr):
        self.weight -= lr * self.grad


class Linear:
    def __init__(self, in_features, out_features, bias=True):
        self.weight = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        self.bias = np.zeros(out_features) if bias else None
        self.grad_weight = np.zeros_like(self.weight)
        self.grad_bias = np.zeros(out_features) if bias else None
    
    def forward(self, x):
        self.x = x
        out = x @ self.weight
        if self.bias is not None:
            out = out + self.bias
        return out
    
    def backward(self, dout):
        self.grad_weight = self.x.reshape(-1, self.x.shape[-1]).T @ dout.reshape(-1, dout.shape[-1])
        if self.bias is not None:
            self.grad_bias = dout.sum(axis=tuple(range(dout.ndim-1)))
        return dout @ self.weight.T
    
    def update(self, lr):
        self.weight -= lr * self.grad_weight
        if self.bias is not None:
            self.bias -= lr * self.grad_bias


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.grad_gamma = np.zeros(d_model)
        self.grad_beta = np.zeros(d_model)
    
    def forward(self, x):
        self.x_shape = x.shape
        x = x.reshape(-1, x.shape[-1])
        self.mean = x.mean(axis=0)
        self.var = x.var(axis=0) + self.eps
        x_norm = (x - self.mean) / np.sqrt(self.var)
        self.x_norm = x_norm
        out = x_norm * self.gamma + self.beta
        return out.reshape(self.x_shape)
    
    def backward(self, dout):
        dout = dout.reshape(-1, dout.shape[-1])
        N = dout.shape[0]
        self.grad_gamma = (dout * self.x_norm).sum(axis=0)
        self.grad_beta = dout.sum(axis=0)
        dx_norm = dout * self.gamma
        dvar = (dx_norm * (self.x_norm - self.mean) * -0.5 * np.power(self.var, -1.5)).sum(axis=0)
        dmean = (-dx_norm / np.sqrt(self.var)).sum(axis=0) + dvar * (-2 * (self.x_norm - self.mean)).sum(axis=0) / N
        dx = dx_norm / np.sqrt(self.var) + dvar * 2 * (self.x_norm - self.mean) / N + dmean / N
        return dx.reshape(self.x_shape)
    
    def update(self, lr):
        self.gamma -= lr * self.grad_gamma
        self.beta -= lr * self.grad_beta


class MLP:
    def __init__(self, d_model, d_ff):
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)
    
    def forward(self, x, training=True):
        self.x = x
        x = self.fc1.forward(x)
        self.x_act = gelu(x)
        return self.fc2.forward(self.x_act)
    
    def backward(self, dout):
        dout = self.fc2.backward(dout)
        dout = dout * gelu_backward(self.x_act)
        return self.fc1.backward(dout)
    
    def update(self, lr):
        self.fc1.update(lr)
        self.fc2.update(lr)


class MultiHeadAttention:
    def __init__(self, d_model, n_head, dropout=0.1):
        assert d_model % n_head == 0
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_model // n_head
        self.wq = Linear(d_model, d_model)
        self.wk = Linear(d_model, d_model)
        self.wv = Linear(d_model, d_model)
        self.wo = Linear(d_model, d_model)
        self.dropout = dropout
    
    def _causal_mask(self, T):
        return np.triu(np.ones((T, T)) * -1e9, k=1)
    
    def forward(self, x, training=True):
        B, T, D = x.shape
        Q = self.wq.forward(x)
        K = self.wk.forward(x)
        V = self.wv.forward(x)
        def split_heads(x):
            return x.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        Q_h = split_heads(Q)
        K_h = split_heads(K)
        V_h = split_heads(V)
        scores = Q_h @ K_h.transpose(0, 1, 3, 2) / np.sqrt(self.d_head)
        mask = self._causal_mask(T)
        scores = scores + mask
        scores_max = np.max(scores, axis=-1, keepdims=True)
        attn = np.exp(scores - scores_max)
        attn = attn / (attn.sum(axis=-1, keepdims=True) + 1e-9)
        if training and self.dropout > 0:
            mask_drop = (np.random.rand(*attn.shape) > self.dropout).astype(float)
            attn = attn * mask_drop / (1 - self.dropout + 1e-9)
        self.attn = attn
        self.V_h = V_h
        self.Q_h = Q_h
        self.K_h = K_h
        out = (attn @ V_h).transpose(0, 2, 1, 3).reshape(B, T, D)
        return self.wo.forward(out)
    
    def backward(self, dout):
        B, T, D = dout.shape
        dout = self.wo.backward(dout)
        dout = dout.reshape(B, T, self.n_head, self.d_head).transpose(0, 2, 1, 3)
        dV_h = self.attn.transpose(0, 1, 3, 2) @ dout
        d_scores = dout @ self.V_h.transpose(0, 1, 3, 2)
        attn = self.attn
        d_scores = attn * (d_scores - np.sum(attn * d_scores, axis=-1, keepdims=True))
        dQ_h = d_scores @ self.K_h / np.sqrt(self.d_head)
        dK_h = d_scores.transpose(0, 1, 3, 2) @ self.Q_h / np.sqrt(self.d_head)
        def merge_heads(x):
            return x.transpose(0, 2, 1, 3).reshape(B, T, D)
        dQ = merge_heads(dQ_h)
        dK = merge_heads(dK_h)
        dV = merge_heads(dV_h)
        return self.wq.backward(dQ) + self.wk.backward(dK) + self.wv.backward(dV)
    
    def update(self, lr):
        self.wq.update(lr)
        self.wk.update(lr)
        self.wv.update(lr)
        self.wo.update(lr)


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff, dropout=0.1):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head, dropout)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)
        self.dropout = dropout
    
    def forward(self, x, training=True):
        x_norm = self.ln1.forward(x)
        x_attn = self.attn.forward(x_norm, training)
        if training and self.dropout > 0:
            x_attn = x_attn * (np.random.rand(*x_attn.shape) > self.dropout) / (1 - self.dropout + 1e-9)
        x = x + x_attn
        x_norm = self.ln2.forward(x)
        x_mlp = self.mlp.forward(x_norm, training)
        if training and self.dropout > 0:
            x_mlp = x_mlp * (np.random.rand(*x_mlp.shape) > self.dropout) / (1 - self.dropout + 1e-9)
        x = x + x_mlp
        return x
    
    def backward(self, dout):
        dout = self.mlp.backward(dout)
        dout = self.ln2.backward(dout)
        dout = self.attn.backward(dout)
        dout = self.ln1.backward(dout)
        return dout
    
    def update(self, lr):
        self.ln1.update(lr)
        self.attn.update(lr)
        self.ln2.update(lr)
        self.mlp.update(lr)


class TransformerLM:
    def __init__(self, vocab_size, d_model=64, n_head=2, n_layer=2, d_ff=128, max_seq_len=64, dropout=0.1):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_seq_len, d_model)
        self.blocks = [TransformerBlock(d_model, n_head, d_ff, dropout) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size, bias=False)
    
    def forward(self, x, training=True):
        B, T = x.shape
        tok_emb = self.token_emb.forward(x)
        pos = np.arange(T)[None, :]
        pos_emb = self.pos_emb.forward(pos)
        x = tok_emb + pos_emb
        for block in self.blocks:
            x = block.forward(x, training)
        x = self.ln_f.forward(x)
        return self.head.forward(x)
    
    def backward(self, dout):
        dout = self.head.backward(dout)
        dout = self.ln_f.backward(dout)
        for block in reversed(self.blocks):
            dout = block.backward(dout)
        self.pos_emb.backward(dout)
        self.token_emb.backward(dout)
    
    def update(self, lr):
        self.token_emb.update(lr)
        self.pos_emb.update(lr)
        for block in self.blocks:
            block.update(lr)
        self.ln_f.update(lr)
        self.head.update(lr)


def cross_entropy_loss(logits, targets):
    B, T, V = logits.shape
    logits_max = np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits - logits_max)
    probs = exp_logits / (exp_logits.sum(axis=-1, keepdims=True) + 1e-9)
    targets_flat = targets.reshape(-1)
    probs_flat = probs.reshape(-1, V)
    one_hot = np.zeros_like(probs_flat)
    one_hot[np.arange(len(targets_flat)), targets_flat] = 1
    loss = -np.sum(one_hot * np.log(probs_flat + 1e-9)) / (B * T)
    dout = (probs - one_hot).reshape(B, T, V) / (B * T)
    return loss, dout


def compute_accuracy(logits, targets):
    preds = np.argmax(logits, axis=-1)
    correct = (preds == targets).sum()
    total = targets.size
    return correct / total if total > 0 else 0.0


class Adam:
    def __init__(self, model, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.model = model
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = {}
        self.v = {}
        for name, param, grad in self._get_params(model):
            self.m[name] = np.zeros_like(param)
            self.v[name] = np.zeros_like(param)
    
    def _get_params(self, obj, prefix='model'):
        for attr in dir(obj):
            if attr.startswith('_'): continue
            val = getattr(obj, attr)
            if isinstance(val, np.ndarray) and hasattr(obj, 'grad') and hasattr(getattr(obj, 'grad', None), 'shape') and getattr(obj, 'grad').shape == val.shape:
                yield f"{prefix}.{attr}", val, getattr(obj, 'grad')
            elif hasattr(val, 'weight'):
                yield from self._get_params(val, f"{prefix}.{attr}")
    
    def step(self):
        self.t += 1
        lr_t = self.lr * np.sqrt(1 - self.beta2**self.t) / (1 - self.beta1**self.t)
        for name, param, grad in self._get_params(self.model):
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * grad**2
            param -= lr_t * self.m[name] / (np.sqrt(self.v[name]) + self.eps)


def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    ids = tokenizer.encode(prompt)
    ids = ids[-model.max_seq_len:]
    eos_id = tokenizer.eos_token_id
    for _ in range(max_new_tokens):
        x = np.array([ids])
        logits = model.forward(x, training=False)[0, -1, :]
        if temperature != 1.0:
            logits = logits / temperature
        if top_k is not None:
            top_k = min(top_k, len(logits))
            top_idx = np.argsort(logits)[-top_k:]
            mask = np.ones_like(logits) * -1e9
            mask[top_idx] = 0
            logits = logits + mask
        probs = np.exp(logits - np.max(logits))
        probs = probs / probs.sum()
        next_id = np.random.choice(len(probs), p=probs)
        ids.append(int(next_id))
        if next_id == eos_id:
            break
    return tokenizer.decode(ids)


def plot_metrics(train_losses, val_losses, train_accs, val_accs, path='metrics.png'):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    ax1.plot(train_losses, label='Train Loss', color='blue')
    ax1.plot(val_losses, label='Val Loss', color='red')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Cross-Entropy Loss')
    ax1.legend()
    ax1.grid(True)
    ax2.plot(train_accs, label='Train Accuracy', color='green')
    ax2.plot(val_accs, label='Val Accuracy', color='orange')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Token Prediction Accuracy')
    ax2.legend()
    ax2.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    fig_loss, ax_loss = plt.subplots(1, 1, figsize=(8, 5))
    ax_loss.plot(train_losses, label='Train Loss', color='blue')
    ax_loss.plot(val_losses, label='Val Loss', color='red')
    ax_loss.set_xlabel('Epoch')
    ax_loss.set_ylabel('Loss')
    ax_loss.set_title('Loss Curve')
    ax_loss.legend()
    ax_loss.grid(True)
    plt.savefig(path.replace('.png', '_loss.png'), dpi=150)
    plt.close()
    fig_acc, ax_acc = plt.subplots(1, 1, figsize=(8, 5))
    ax_acc.plot(train_accs, label='Train Accuracy', color='green')
    ax_acc.plot(val_accs, label='Val Accuracy', color='orange')
    ax_acc.set_xlabel('Epoch')
    ax_acc.set_ylabel('Accuracy')
    ax_acc.set_title('Accuracy Curve')
    ax_acc.legend()
    ax_acc.grid(True)
    plt.savefig(path.replace('.png', '_acc.png'), dpi=150)
    plt.close()


def train():
    np.random.seed(config.SEED)
    try:
        tokenizer = BPETokenizer.load(config.TOKENIZER_PATH)
    except:
        tokenizer = BPETokenizer()
        data_path = find_data_file()
        if data_path is None:
            raise FileNotFoundError("data.txt not found.")
        tokenizer.train(data_path, num_merges=config.NUM_MERGES, val_split=config.VAL_SPLIT)
        tokenizer.save(config.TOKENIZER_PATH)
    config.VOCAB_SIZE = len(tokenizer)
    
    use_streaming = getattr(config, 'USE_STREAMING', False)
    
    if use_streaming:
        print("Using streaming data loader...")
        data_loader = load_data_generator(tokenizer, config.MAX_SEQ_LEN, config.BATCH_SIZE, chunk_size=500)
        (train_X, train_Y), (val_X, val_Y) = load_data_chunked(tokenizer, config.MAX_SEQ_LEN, chunk_size=1000)
    else:
        (train_X, train_Y), (val_X, val_Y) = load_data_chunked(tokenizer, config.MAX_SEQ_LEN, chunk_size=1000)
    
    print(f"Train samples: {len(train_X)}, Val samples: {len(val_X)}")
    print(f"Vocab size: {config.VOCAB_SIZE}, EOS token ID: {tokenizer.eos_token_id}")
    
    model = TransformerLM(
        vocab_size=config.VOCAB_SIZE,
        d_model=config.D_MODEL,
        n_head=config.N_HEAD,
        n_layer=config.N_LAYER,
        d_ff=config.D_FF,
        max_seq_len=config.MAX_SEQ_LEN,
        dropout=config.DROPOUT
    )
    total_params = sum(p.size for _, p, _ in Adam(model)._get_params(model))
    print(f"Total parameters: {total_params:,}")
    
    optimizer = Adam(model, lr=config.LR, beta1=config.BETA1, beta2=config.BETA2, eps=config.EPS)
    train_losses, val_losses = [], []
    train_accs, val_accs = [], []
    
    for epoch in range(config.EPOCHS):
        epoch_losses, epoch_accs = [], []
        
        if use_streaming:
            data_loader = load_data_generator(tokenizer, config.MAX_SEQ_LEN, config.BATCH_SIZE, chunk_size=500)
            total_batches = len(train_X) // config.BATCH_SIZE
            for batch_idx, (x, y) in enumerate(tqdm(data_loader, desc=f"Epoch {epoch+1}/{config.EPOCHS}", total=total_batches)):
                if len(x) < config.BATCH_SIZE:
                    continue
                logits = model.forward(x, training=True)
                loss, dout = cross_entropy_loss(logits, y)
                acc = compute_accuracy(logits, y)
                model.backward(dout)
                for name, param, grad in optimizer._get_params(model):
                    norm = np.linalg.norm(grad)
                    if norm > config.GRAD_CLIP:
                        grad *= config.GRAD_CLIP / norm
                optimizer.step()
                model.update(optimizer.lr)
                epoch_losses.append(loss)
                epoch_accs.append(acc)
        else:
            perm = np.random.permutation(len(train_X))
            for idx in tqdm(perm, desc=f"Epoch {epoch+1}/{config.EPOCHS}"):
                x, y = train_X[idx:idx+1], train_Y[idx:idx+1]
                logits = model.forward(x, training=True)
                loss, dout = cross_entropy_loss(logits, y)
                acc = compute_accuracy(logits, y)
                model.backward(dout)
                for name, param, grad in optimizer._get_params(model):
                    norm = np.linalg.norm(grad)
                    if norm > config.GRAD_CLIP:
                        grad *= config.GRAD_CLIP / norm
                optimizer.step()
                model.update(optimizer.lr)
                epoch_losses.append(loss)
                epoch_accs.append(acc)
        
        val_loss, val_acc = 0, 0
        val_limit = min(len(val_X), config.VAL_SAMPLES)
        for idx in range(val_limit):
            x, y = val_X[idx:idx+1], val_Y[idx:idx+1]
            logits = model.forward(x, training=False)
            loss, _ = cross_entropy_loss(logits, y)
            acc = compute_accuracy(logits, y)
            val_loss += loss
            val_acc += acc
        val_loss /= val_limit if val_limit > 0 else 1
        val_acc /= val_limit if val_limit > 0 else 1
        avg_train_loss = np.mean(epoch_losses) if epoch_losses else 0
        avg_train_acc = np.mean(epoch_accs) if epoch_accs else 0
        train_losses.append(avg_train_loss)
        val_losses.append(val_loss)
        train_accs.append(avg_train_acc)
        val_accs.append(val_acc)
        print(f"Epoch {epoch+1}: loss={avg_train_loss:.4f}, acc={avg_train_acc:.4f} | val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")
    
    np.save(f"{config.SAVE_DIR}/train_losses.npy", train_losses)
    np.save(f"{config.SAVE_DIR}/val_losses.npy", val_losses)
    np.save(f"{config.SAVE_DIR}/train_accs.npy", train_accs)
    np.save(f"{config.SAVE_DIR}/val_accs.npy", val_accs)
    plot_metrics(train_losses, val_losses, train_accs, val_accs, f"{config.LOG_DIR}/metrics.png")
    params = {}
    def collect(obj, prefix):
        for attr in dir(obj):
            if not attr.startswith('_') and hasattr(getattr(obj, attr), 'shape'):
                val = getattr(obj, attr)
                if isinstance(val, np.ndarray):
                    params[f"{prefix}.{attr}"] = val.copy()
            elif hasattr(getattr(obj, attr), 'weight'):
                collect(getattr(obj, attr), f"{prefix}.{attr}")
    collect(model, 'model')
    np.savez(f"{config.SAVE_DIR}/model_weights.npz", **{k: v for k, v in params.items() if v.size < 1e7})
    print("Training complete!")
    print(f"Final: train_loss={train_losses[-1]:.4f}, train_acc={train_accs[-1]:.4f}")
    print(f"Final: val_loss={val_losses[-1]:.4f}, val_acc={val_accs[-1]:.4f}")
    print(f"Plots saved to {config.LOG_DIR}/")


def sample(prompt, max_new_tokens=None, temperature=None, top_k=None, checkpoint=None):
    if max_new_tokens is None: max_new_tokens = config.MAX_NEW_TOKENS
    if temperature is None: temperature = config.TEMPERATURE
    if top_k is None: top_k = config.TOP_K
    if checkpoint is None: checkpoint = f"{config.SAVE_DIR}/model_weights.npz"
    tokenizer = BPETokenizer.load(config.TOKENIZER_PATH)
    config.VOCAB_SIZE = len(tokenizer)
    model = TransformerLM(
        vocab_size=config.VOCAB_SIZE,
        d_model=config.D_MODEL,
        n_head=config.N_HEAD,
        n_layer=config.N_LAYER,
        d_ff=config.D_FF,
        max_seq_len=config.MAX_SEQ_LEN,
        dropout=0.0
    )
    try:
        data = np.load(checkpoint, allow_pickle=True)
        print(f"Loaded weights from {checkpoint}")
    except:
        print("Warning: Could not load weights")
    result = generate(model, tokenizer, prompt, max_new_tokens, temperature, top_k)
    return result
