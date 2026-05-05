import numpy as np
import argparse
import json
import os
import sys
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))
from model import TransformerLM, loss_fn, AdamOptimizer
from dataset import build_dataset
from bpe_tokenizer import BPETokenizer
from utils import load_data, split_corpus


def get_batch(x, y, batch_size, rng):
    idx = rng.randint(0, len(x), size=batch_size)
    return x[idx], y[idx]


def eval_loss(model, x, y, batch_size=32, n_batches=10, rng=None):
    if rng is None:
        rng = np.random.RandomState(0)
    losses = []
    for _ in range(n_batches):
        xb, yb = get_batch(x, y, batch_size, rng)
        logits = model.forward(xb)
        loss, _ = loss_fn(logits, yb)
        losses.append(float(loss))
    return float(np.mean(losses))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="../task3/data.txt")
    parser.add_argument("--tokenizer", type=str, default="../task3/bpe_model.json")
    parser.add_argument("--n_merges", type=int, default=2000)
    parser.add_argument("--d_model", type=int, default=128)
    parser.add_argument("--n_head", type=int, default=4)
    parser.add_argument("--n_layer", type=int, default=2)
    parser.add_argument("--T", type=int, default=64)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--steps_per_epoch", type=int, default=100)
    parser.add_argument("--save", type=str, default="gpt_model")
    parser.add_argument("--plot", type=str, default="loss_curve.png")
    args = parser.parse_args()

    if not os.path.exists(args.tokenizer):
        print(f"токенайзер не найден, обучаем BPE ({args.n_merges} merges)...")
        from bpe_tokenizer import BPETokenizer
        lines = load_data(args.data)
        train_lines, _ = split_corpus(lines)
        tok = BPETokenizer()
        tok.train(train_lines, num_merges=args.n_merges)
        tok.save(args.tokenizer)
        print(f"токенайзер сохранён: {args.tokenizer}, vocab={len(tok.vocab)}")

    print("строим датасет...")
    x_train, y_train, x_val, y_val, tokenizer = build_dataset(args.data, args.tokenizer, args.T)
    print(f"train blocks: {len(x_train)}, val blocks: {len(x_val)}")

    vocab_size = len(tokenizer.vocab)
    print(f"vocab_size={vocab_size}, d_model={args.d_model}, n_head={args.n_head}, n_layer={args.n_layer}, T={args.T}")

    rng = np.random.RandomState(42)
    model = TransformerLM(vocab_size, args.d_model, args.n_head, args.n_layer, args.T)
    optimizer = AdamOptimizer(model.params(), lr=args.lr, weight_decay=1e-2)

    train_losses = []
    val_losses = []

    print("начинаем обучение...")
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        ep_losses = []

        for step in tqdm(range(args.steps_per_epoch), desc=f"epoch {epoch}"):
            xb, yb = get_batch(x_train, y_train, args.batch_size, rng)

            logits = model.forward(xb)
            loss, dlogits = loss_fn(logits, yb)

            model.zero_grad()
            model.backward(dlogits)
            optimizer.step()

            ep_losses.append(float(loss))

        train_loss = float(np.mean(ep_losses))
        val_loss = eval_loss(model, x_val, y_val, rng=rng)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        dt = time.time() - t0
        print(f"epoch {epoch:3d} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | {dt:.1f}s")

    model.save(args.save)
    print(f"модель сохранена: {args.save}.npz")

    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, label="train loss")
    plt.plot(val_losses, label="val loss")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.title("Training curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.plot)
    print(f"график сохранён: {args.plot}")

    cfg = {
        "vocab_size": vocab_size,
        "d_model": args.d_model,
        "n_head": args.n_head,
        "n_layer": args.n_layer,
        "T": args.T,
    }
    with open(args.save + "_config.json", "w") as f:
        json.dump(cfg, f, indent=2)


if __name__ == "__main__":
    main()