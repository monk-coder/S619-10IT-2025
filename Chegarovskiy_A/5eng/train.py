"""
Обучение GPT на текстовом корпусе.
"""

import os
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.cuda.amp import GradScaler

from model import GPT


class TextDataset(Dataset):
    def __init__(self, data, seq_len):
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + 1:idx + self.seq_len + 1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)


def encode_text(text, vocab, merges, word_end):
    tokens = []
    words = text.split()
    for word in words:
        chars = list(word) + [word_end]
        tokens.extend(chars)
    for a, b in merges:
        new_token = a + b
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == a and tokens[i+1] == b:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return [vocab.get(t, 0) for t in tokens]


def load_bpe(path='bpe_8000.json'):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['vocab'], [tuple(m) for m in data['merges']], data['word_end']


def create_causal_mask(seq_len, device):
    return torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data.txt')
    parser.add_argument('--bpe_path', type=str, default='bpe_8000.json')
    parser.add_argument('--seq_len', type=int, default=128)
    parser.add_argument('--d_model', type=int, default=384)
    parser.add_argument('--n_head', type=int, default=8)
    parser.add_argument('--n_layer', type=int, default=4)
    parser.add_argument('--d_ff', type=int, default=768)
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--max_iters', type=int, default=50000)
    parser.add_argument('--eval_interval', type=int, default=500)
    parser.add_argument('--warmup_iters', type=int, default=5000)
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--grad_clip', type=float, default=1.0)
    parser.add_argument('--weight_decay', type=float, default=0.01)
    parser.add_argument('--save_dir', type=str, default='checkpoints')

    args = parser.parse_args()

    os.makedirs(args.save_dir, exist_ok=True)
    device = torch.device(args.device)
    print(f"Устройство: {device}")

    print("Загрузка BPE...")
    vocab, merges, word_end = load_bpe(args.bpe_path)
    vocab_size = len(vocab)
    print(f"  Словарь: {vocab_size} токенов")

    print("Загрузка и токенизация текста...")
    with open(args.data_path, 'r', encoding='utf-8') as f:
        text = f.read()

    tokens = encode_text(text, vocab, merges, word_end)
    data = np.array(tokens, dtype=np.int32)
    print(f"  Всего токенов: {len(data)}")

    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    print(f"  Train: {len(train_data)}, Val: {len(val_data)}")

    train_dataset = TextDataset(train_data, args.seq_len)
    val_dataset = TextDataset(val_data, args.seq_len)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, pin_memory=(device.type=='cuda'))
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, pin_memory=(device.type=='cuda'))

    print("Создание модели...")
    model = GPT(
        vocab_size=vocab_size,
        d_model=args.d_model,
        n_head=args.n_head,
        n_layer=args.n_layer,
        d_ff=args.d_ff,
        seq_len=args.seq_len
    ).to(device)

    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    def lr_lambda(step):
        if step < args.warmup_iters:
            return step / args.warmup_iters
        else:
            denom = max(1, args.max_iters - args.warmup_iters)
            return 0.5 * (1 + np.cos(np.pi * (step - args.warmup_iters) / denom))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    scaler = GradScaler() if device.type == 'cuda' else None

    causal_mask = create_causal_mask(args.seq_len, device)

    print(f"\nОбучение {args.max_iters} итераций...")
    print("-" * 60)

    train_losses = []
    val_losses = []
    val_perplexities = []
    best_val_loss = float('inf')

    iterator = iter(train_loader)

    for step in tqdm(range(args.max_iters), desc="Training"):
        try:
            x, y = next(iterator)
        except StopIteration:
            iterator = iter(train_loader)
            x, y = next(iterator)

        x, y = x.to(device), y.to(device)

        optimizer.zero_grad(set_to_none=True)

        if scaler:
            with torch.autocast(device_type=device.type):
                logits = model(x, causal_mask)
                loss = nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(x, causal_mask)
            loss = nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()

        scheduler.step()
        train_losses.append(loss.item())

        if (step + 1) % args.eval_interval == 0:
            model.eval()
            val_loss_total = 0
            val_steps = 0

            with torch.no_grad():
                for x_val, y_val in val_loader:
                    x_val, y_val = x_val.to(device), y_val.to(device)
                    logits_val = model(x_val, causal_mask)
                    v_loss = nn.functional.cross_entropy(logits_val.view(-1, logits_val.size(-1)), y_val.view(-1))
                    val_loss_total += v_loss.item()
                    val_steps += 1

            avg_val_loss = val_loss_total / max(val_steps, 1)
            perplexity = np.exp(min(avg_val_loss, 20))
            val_losses.append(avg_val_loss)
            val_perplexities.append(perplexity)

            print(f"\nStep {step+1}/{args.max_iters} | Train Loss: {loss.item():.4f} | Val Loss: {avg_val_loss:.4f} | PPL: {perplexity:.2f}")

            checkpoint_path = os.path.join(args.save_dir, f'model_step_{step+1}.pt')
            torch.save(model.state_dict(), checkpoint_path)

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), os.path.join(args.save_dir, 'best_model.pt'))
                print(f"  ✅ Лучшая модель (PPL: {perplexity:.2f})")

            model.train()

    print("\nСохранение графиков...")
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    smoothed = [sum(train_losses[i:i+50])/50 for i in range(0, len(train_losses)-50, 50)]
    plt.plot(range(0, len(train_losses)-50, 50), smoothed, alpha=0.7)
    plt.xlabel('Step')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    steps_x = range(args.eval_interval, args.max_iters + 1, args.eval_interval)
    plt.plot(steps_x[:len(val_perplexities)], val_perplexities, 'o-')
    plt.xlabel('Step')
    plt.ylabel('Perplexity')
    plt.title('Validation Perplexity')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(args.save_dir, 'training_curves.png'), dpi=150)

    torch.save(model.state_dict(), os.path.join(args.save_dir, 'final_model.pt'))

    print("\n" + "=" * 60)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)
    print(f"Лучший PPL: {min(val_perplexities):.2f}")
    print(f"Модели в {args.save_dir}/")
    print("=" * 60)


if __name__ == '__main__':
    main()