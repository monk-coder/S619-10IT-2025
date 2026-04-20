import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
import time
import os
from model import GPT
from config import Config, get_args
import pickle


class Trainer:
    def __init__(self, model, config, args):
        self.model = model
        self.config = config
        self.args = args
        self.device = torch.device(args.device if torch.cuda.is_available() and args.device == 'cuda' else 'cpu')
        self.model.to(self.device)

        # Оптимизатор с меньшим weight decay для CPU
        self.optimizer = AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.01)

        total_iters = args.max_iters
        warmup_iters = args.warmup_iters if args.warmup_iters else int(0.1 * total_iters)

        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=total_iters - warmup_iters)
        self.warmup_iters = warmup_iters

        # Mixed precision только для GPU
        if self.device.type == 'cuda':
            self.scaler = torch.amp.GradScaler('cuda')
        else:
            self.scaler = None

        self.best_val_loss = float('inf')
        os.makedirs('checkpoints', exist_ok=True)

    def train_step(self, x, y):
        self.optimizer.zero_grad()

        # Forward pass
        _, loss = self.model(x, y)

        # Backward pass
        if self.scaler is not None:
            self.scaler.scale(loss).backward()
            if self.args.gradient_clip > 0:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.args.gradient_clip)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            if self.args.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.args.gradient_clip)
            self.optimizer.step()

        return loss.item()

    def update_lr(self, iteration):
        if iteration < self.warmup_iters:
            lr = self.args.lr * (iteration + 1) / self.warmup_iters
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = lr
        else:
            self.scheduler.step()

    @torch.no_grad()
    def evaluate(self, val_loader, eval_iters=50):
        self.model.eval()
        losses = []

        for i, (x, y) in enumerate(val_loader):
            if i >= eval_iters:
                break
            x, y = x.to(self.device), y.to(self.device)
            _, loss = self.model(x, y)
            losses.append(loss.item())

        self.model.train()
        mean_loss = np.mean(losses)
        perplexity = np.exp(mean_loss)
        return mean_loss, perplexity

    def save_checkpoint(self, iteration, is_best=False):
        checkpoint = {
            'iteration': iteration,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'config': self.config,
            'args': self.args
        }

        if self.scaler is not None:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()

        if is_best:
            path = 'checkpoints/best_model.pt'
        else:
            path = f'checkpoints/model_iter_{iteration}.pt'

        torch.save(checkpoint, path)

        if is_best:
            print(f"Best model saved with loss: {self.best_val_loss:.4f}")

    def train(self, train_loader, val_loader):
        print(f"Training on {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")

        train_iter = iter(train_loader)
        start_time = time.time()

        for iteration in range(self.args.max_iters):
            try:
                x, y = next(train_iter)
            except StopIteration:
                train_iter = iter(train_loader)
                x, y = next(train_iter)

            x, y = x.to(self.device), y.to(self.device)

            self.update_lr(iteration)
            loss = self.train_step(x, y)

            if iteration % 50 == 0:
                current_lr = self.optimizer.param_groups[0]['lr']
                elapsed = time.time() - start_time
                print(f"Iter {iteration:4d} | Loss: {loss:.4f} | LR: {current_lr:.6f} | Time: {elapsed:.1f}s")

            if (iteration + 1) % self.args.eval_interval == 0:
                val_loss, perplexity = self.evaluate(val_loader, min(self.args.eval_iters, len(val_loader)))
                print(f"\nEvaluation at iteration {iteration}:")
                print(f"Val Loss: {val_loss:.4f} | Perplexity: {perplexity:.2f}\n")

                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.save_checkpoint(iteration, is_best=True)

            if (iteration + 1) % self.args.save_interval == 0:
                self.save_checkpoint(iteration)

        print(f"\nTraining completed! Best validation loss: {self.best_val_loss:.4f}")
        print(f"Best perplexity: {np.exp(self.best_val_loss):.2f}")


def load_data(data_path, block_size, batch_size, device='cpu'):
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chars = sorted(list(set(text)))
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}

    data = [stoi[ch] for ch in text]
    data = torch.tensor(data, dtype=torch.long)

    n = int(0.9 * len(data))
    train_data = data[:n]
    val_data = data[n:]

    train_dataset = CharDataset(train_data, block_size)
    val_dataset = CharDataset(val_data, block_size)

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=0
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=0
    )

    return train_loader, val_loader, len(chars), stoi, itos


class CharDataset(torch.utils.data.Dataset):
    def __init__(self, data, block_size):
        self.data = data
        self.block_size = block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return x.clone().detach(), y.clone().detach()


def main():
    args = get_args()
    config = Config()

    # Проверяем существование файла data.txt
    if not os.path.exists('data.txt'):
        print("Error: data.txt not found!")
        print("Please create data.txt with training text.")
        return

    print(f"Loading data from data.txt...")
    train_loader, val_loader, vocab_size, stoi, itos = load_data(
        'data.txt', config.block_size, args.batch_size, args.device
    )

    print(f"Vocabulary size: {vocab_size}")
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")

    config.vocab_size = vocab_size

    model = GPT(config)

    trainer = Trainer(model, config, args)

    print(f"\nStarting training for {args.max_iters} iterations...")
    trainer.train(train_loader, val_loader)

    # Сохраняем словарь
    with open('vocab.pkl', 'wb') as f:
        pickle.dump((stoi, itos), f)

    print("\nTraining completed! Vocabulary saved to vocab.pkl")


if __name__ == '__main__':
    main()