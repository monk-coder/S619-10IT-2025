import os
import sys
import math
import time
import json

import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))

from config import get_config
from model import TransformerLM
from data import load_corpus, DataLoader


def get_lr(step, max_iters, warmup_iters, lr):
    if step < warmup_iters:
        return lr * step / max(warmup_iters, 1)
    progress = (step - warmup_iters) / max(max_iters - warmup_iters, 1)
    return lr * 0.5 * (1.0 + math.cos(math.pi * progress))


@torch.no_grad()
def eval_loss(model, loader, eval_iters, amp, dev_type):
    model.eval()
    losses = []
    for _ in range(eval_iters):
        xb, yb = loader.get_batch()
        with torch.amp.autocast(device_type=dev_type, enabled=amp):
            _, loss = model(xb, yb)
        losses.append(loss.item())
    model.train()
    avg = sum(losses) / len(losses)
    return avg, math.exp(avg)


def save_checkpoint(model, optimizer, scaler, step, val_loss, cfg, path):
    torch.save({
        "step": step,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
        "val_loss": val_loss,
        "config": {
            "vocab_size": model.tok_emb.num_embeddings,
            "d_model": model.tok_emb.embedding_dim,
            "n_head": model.blocks[0].attn.n_head,
            "n_layer": len(model.blocks),
            "T": model.T,
            "dropout": cfg.dropout,
        }
    }, path)


def main():
    cfg = get_config()
    torch.manual_seed(cfg.seed)

    device = cfg.device
    dev_type = "cuda" if "cuda" in str(device) else "cpu"
    use_amp = cfg.amp and dev_type == "cuda"

    print(f"device={device}, amp={use_amp}")

    train_ids, val_ids, vocab_size, tok = load_corpus(cfg.data, cfg.tokenizer)

    train_loader = DataLoader(train_ids, cfg.T, cfg.batch_size, device)
    val_loader = DataLoader(val_ids, cfg.T, max(cfg.batch_size // 2, 1), device)

    model = TransformerLM(
        vocab_size=vocab_size,
        d_model=cfg.d_model,
        n_head=cfg.n_head,
        n_layer=cfg.n_layer,
        T=cfg.T,
        dropout=cfg.dropout,
    ).to(device)

    if cfg.compile:
        print("compiling model...")
        model = torch.compile(model)

    print(f"params: {model.num_params() / 1e6:.2f}M")

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=cfg.lr,
        betas=(cfg.beta1, cfg.beta2),
        weight_decay=cfg.weight_decay,
    )

    scaler = torch.amp.GradScaler(enabled=use_amp)

    train_log = []
    val_log = []
    best_val_loss = float("inf")
    t0 = time.time()

    for step in range(1, cfg.max_iters + 1):
        lr = get_lr(step, cfg.max_iters, cfg.warmup_iters, cfg.lr)
        for g in optimizer.param_groups:
            g["lr"] = lr

        xb, yb = train_loader.get_batch()

        with torch.amp.autocast(device_type=dev_type, enabled=use_amp):
            _, loss = model(xb, yb)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.max_norm)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)

        train_log.append((step, loss.item()))

        if step % cfg.eval_interval == 0 or step == cfg.max_iters:
            val_loss, val_ppl = eval_loss(model, val_loader, cfg.eval_iters, use_amp, dev_type)
            elapsed = time.time() - t0
            val_log.append((step, val_loss, val_ppl))

            print(f"step {step:5d} | train={loss.item():.4f} | val={val_loss:.4f} | ppl={val_ppl:.2f} | lr={lr:.2e} | {elapsed:.0f}s")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                save_checkpoint(model, optimizer, scaler, step, val_loss, cfg,
                                os.path.join(cfg.checkpoint_dir, "best.pt"))
                print(f"  -> best checkpoint (val={val_loss:.4f})")

        if step % cfg.save_interval == 0:
            save_checkpoint(model, optimizer, scaler, step, loss.item(), cfg,
                            os.path.join(cfg.checkpoint_dir, f"ckpt_{step:05d}.pt"))

    save_checkpoint(model, optimizer, scaler, cfg.max_iters, best_val_loss, cfg,
                    os.path.join(cfg.checkpoint_dir, "last.pt"))
    print("done")

    steps = [s for s, _ in train_log]
    t_losses = [l for _, l in train_log]
    v_steps = [s for s, _, _ in val_log]
    v_losses = [l for _, l, _ in val_log]
    v_ppls = [p for _, _, p in val_log]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(steps, t_losses, alpha=0.4, label="train loss")
    ax1.plot(v_steps, v_losses, linewidth=2, label="val loss")
    ax1.set_xlabel("step")
    ax1.legend()
    ax1.set_title("Loss")

    ax2.plot(v_steps, v_ppls, linewidth=2, color="orange")
    ax2.set_xlabel("step")
    ax2.set_ylabel("perplexity")
    ax2.set_title("Val Perplexity")

    plt.tight_layout()
    plt.savefig("loss_curve.png", dpi=120)
    print("plot: loss_curve.png")

    with open("train_log.json", "w") as f:
        json.dump({"train": train_log, "val": val_log}, f)


if __name__ == "__main__":
    main()