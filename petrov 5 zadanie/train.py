import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
import urllib.request
import ssl

import config
from tokenizer import BPETokenizer
from gpt import TransformerLM, cross_entropy_loss, compute_accuracy, Adam

def download_file_from_github(url, save_path):
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        print(f"Downloading data from GitHub: {url}")
        urllib.request.urlretrieve(url, save_path)
        return True
    except Exception as e:
        print(f"Failed to download: {e}")
        return False

def find_data_file():
    if os.path.exists(config.DATA_PATH): return config.DATA_PATH
    if hasattr(config, 'GITHUB_DATA_URL') and config.GITHUB_DATA_URL:
        if download_file_from_github(config.GITHUB_DATA_URL, config.DATA_PATH): return config.DATA_PATH
    for path in ["data.txt", "./data.txt", "../data.txt", "data/data.txt"]:
        if os.path.exists(path): return path
    return None

def stream_lines(file_path, chunk_size=1000):
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.strip():
                lines.append(line)
                if len(lines) >= chunk_size: yield lines; lines = []
    if lines: yield lines

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
            X.append(chunk[:-1]); Y.append(chunk[1:])
    return np.array(X) if X else np.array([]).reshape(0, seq_len), \
           np.array(Y) if Y else np.array([]).reshape(0, seq_len)

def load_data_chunked(tokenizer, seq_len, chunk_size=1000):
    data_path = find_data_file()
    if data_path is None: raise FileNotFoundError("data.txt not found.")
    print(f"Loading data in chunks...")
    all_X, all_Y = [], []
    for chunk_lines in stream_lines(data_path, chunk_size):
        X, Y = create_chunks_from_lines(chunk_lines, tokenizer, seq_len)
        if len(X) > 0: all_X.append(X); all_Y.append(Y)
    if not all_X: raise ValueError("No data samples created.")
    train_X = np.vstack(all_X); train_Y = np.vstack(all_Y)
    split = int(len(train_X) * 0.9)
    return (train_X[:split], train_Y[:split]), (train_X[split:], train_Y[split:])

def plot_metrics(train_losses, val_losses, train_accs, val_accs, path='metrics.png'):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    ax1.plot(train_losses, label='Train Loss', color='blue')
    ax1.plot(val_losses, label='Val Loss', color='red')
    ax1.set_xlabel('Epoch'); ax1.set_ylabel('Loss'); ax1.legend(); ax1.grid(True)
    ax2.plot(train_accs, label='Train Accuracy', color='green')
    ax2.plot(val_accs, label='Val Accuracy', color='orange')
    ax2.set_xlabel('Epoch'); ax2.set_ylabel('Accuracy'); ax2.legend(); ax2.grid(True)
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()

def train():
    np.random.seed(config.SEED)
    print("Loading tokenizer...")
    tokenizer = BPETokenizer.load(config.TOKENIZER_PATH)
    config.VOCAB_SIZE = len(tokenizer)
    print("Loading data...")
    (train_X, train_Y), (val_X, val_Y) = load_data_chunked(tokenizer, config.MAX_SEQ_LEN, config.CHUNK_SIZE)
    print(f"Vocab size: {config.VOCAB_SIZE}, EOS: {tokenizer.eos_token_id}")
    print("Initializing model...")
    model = TransformerLM(config.VOCAB_SIZE, config.D_MODEL, config.N_HEAD, config.N_LAYER, config.D_FF, config.MAX_SEQ_LEN, config.DROPOUT)
    total_params = sum(p.size for _, p, _ in Adam(model)._get_params(model))
    print(f"Total parameters: {total_params:,}")
    optimizer = Adam(model, lr=config.LR, beta1=config.BETA1, beta2=config.BETA2, eps=config.EPS)
    train_losses, val_losses, train_accs, val_accs = [], [], [], []
    print("Starting training...")
    for epoch in range(config.EPOCHS):
        perm = np.random.permutation(len(train_X))
        epoch_losses, epoch_accs = [], []
        for idx in tqdm(perm, desc=f"Epoch {epoch+1}/{config.EPOCHS}"):
            x, y = train_X[idx:idx+1], train_Y[idx:idx+1]
            logits = model.forward(x, training=True)
            loss, dout = cross_entropy_loss(logits, y)
            acc = compute_accuracy(logits, y)
            model.backward(dout)
            for name, param, grad in optimizer._get_params(model):
                norm = np.linalg.norm(grad)
                if norm > config.GRAD_CLIP: grad *= config.GRAD_CLIP / norm
            optimizer.step()
            model.update(optimizer.lr)
            epoch_losses.append(loss); epoch_accs.append(acc)
        val_loss, val_acc = 0, 0
        val_limit = min(len(val_X), config.VAL_SAMPLES)
        for idx in range(val_limit):
            x, y = val_X[idx:idx+1], val_Y[idx:idx+1]
            logits = model.forward(x, training=False)
            loss, _ = cross_entropy_loss(logits, y)
            acc = compute_accuracy(logits, y)
            val_loss += loss; val_acc += acc
        val_loss /= val_limit; val_acc /= val_limit
        avg_train_loss = np.mean(epoch_losses); avg_train_acc = np.mean(epoch_accs)
        train_losses.append(avg_train_loss); val_losses.append(val_loss)
        train_accs.append(avg_train_acc); val_accs.append(val_acc)
        print(f"Epoch {epoch+1}: loss={avg_train_loss:.4f}, acc={avg_train_acc:.4f} | val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")
    print("Saving results...")
    np.save(f"{config.SAVE_DIR}/train_losses.npy", train_losses)
    np.save(f"{config.SAVE_DIR}/val_losses.npy", val_losses)
    plot_metrics(train_losses, val_losses, train_accs, val_accs, f"{config.LOG_DIR}/metrics.png")
    params = model.get_params()
    np.savez(f"{config.SAVE_DIR}/model_weights.npz", **{k: v for k, v in params.items() if v.size < 1e7})
    print("Training complete!")

if __name__ == "__main__":
    train()
