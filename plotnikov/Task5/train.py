import torch
import argparse
import os
import math
import json
import time
import matplotlib.pyplot as plt
from tqdm import tqdm

from models.model import GPT, GPTConfig
from utils.data import get_dataloaders

def get_lr(it, warmup_iters, lr_decay_iters, min_lr, learning_rate):
    if it < warmup_iters: return learning_rate * it / warmup_iters
    if it > lr_decay_iters: return min_lr
    decay_ratio = (it - warmup_iters) / (lr_decay_iters - warmup_iters)
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return min_lr + coeff * (learning_rate - min_lr)

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='../data.txt')
    parser.add_argument('--tokenizer_path', type=str, default='../tokenizer.json')
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--block_size', type=int, default=128)
    parser.add_argument('--n_layer', type=int, default=4)
    parser.add_argument('--n_head', type=int, default=4)
    parser.add_argument('--n_embd', type=int, default=128)
    parser.add_argument('--lr', type=float, default=6e-4)
    parser.add_argument('--max_iters', type=int, default=5000)
    parser.add_argument('--eval_interval', type=int, default=500)
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--ckpt_dir', type=str, default='checkpoints')
    args = parser.parse_args()

    device = torch.device(args.device)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    use_amp = device.type == 'cuda'

    train_loader, val_loader, tokenizer = get_dataloaders(
        args.data_path, args.tokenizer_path, args.block_size, args.batch_size
    )

    config = GPTConfig(
        vocab_size=tokenizer.vocab_size, block_size=args.block_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd
    )
    model = GPT(config).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-1)
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    train_losses, val_losses, iters = [], [], []
    best_val_loss = float('inf')
    train_iter = iter(train_loader)
    warmup_iters = int(0.1 * args.max_iters)

    print(f"🚀 Training on {device} | Params: {sum(p.numel() for p in model.parameters()):,}")
    
    pbar = tqdm(range(args.max_iters), desc="Training")
    for iter_num in pbar:
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_loader)
            x, y = next(train_iter)
        x, y = x.to(device), y.to(device)

        lr = get_lr(iter_num, warmup_iters, args.max_iters, args.lr * 0.1, args.lr)
        for pg in optimizer.param_groups: pg['lr'] = lr

        with torch.cuda.amp.autocast(enabled=use_amp):
            _, loss = model(x, y)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)

        train_losses.append(loss.item())
        iters.append(iter_num)

        if iter_num % args.eval_interval == 0 or iter_num == args.max_iters - 1:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for xv, yv in val_loader:
                    _, vloss = model(xv.to(device), yv.to(device))
                    val_loss += vloss.item()
            val_loss /= len(val_loader)
            val_losses.append(val_loss)
            model.train()

            val_ppl = math.exp(min(val_loss, 20))
            pbar.set_postfix(val_ppl=f"{val_ppl:.2f}", val_loss=f"{val_loss:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save({
                    'iter': iter_num, 'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'config': config.__dict__, 'val_loss': val_loss
                }, os.path.join(args.ckpt_dir, 'best.pt'))

    torch.save({
        'iter': args.max_iters, 'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'config': config.__dict__, 'val_loss': val_loss
    }, os.path.join(args.ckpt_dir, 'final.pt'))

    plt.figure(figsize=(8,5))
    plt.plot(iters, train_losses, label='Train Loss')
    plt.plot(range(0, len(val_losses)*args.eval_interval, args.eval_interval), val_losses, label='Val Loss')
    plt.xlabel('Iterations'); plt.ylabel('Loss')
    plt.legend(); plt.grid(True)
    plt.savefig('loss_curve.png')
    print("✅ Training complete. Loss curve saved.")

if __name__ == '__main__':
    train()