# utils.py
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
import os
import json


def get_lr_scheduler(optimizer, warmup_iters, max_iters):
    """Create cosine decay schedule with warmup"""

    def lr_lambda(step):
        if step < warmup_iters:
            return step / warmup_iters
        else:
            progress = (step - warmup_iters) / (max_iters - warmup_iters)
            return 0.5 * (1 + np.cos(np.pi * progress))

    return LambdaLR(optimizer, lr_lambda)


def compute_perplexity(loss):
    """Compute perplexity from cross-entropy loss"""
    return np.exp(loss)


def save_checkpoint(model, optimizer, scheduler, step, loss, perplexity,
                    config, output_dir, is_best=False):
    """Save checkpoint"""

    checkpoint = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'step': step,
        'loss': loss,
        'perplexity': perplexity,
        'config': vars(config)
    }

    # Regular checkpoint
    checkpoint_path = os.path.join(output_dir, f'checkpoint_{step:06d}.pt')
    torch.save(checkpoint, checkpoint_path)

    # Best checkpoint
    if is_best:
        best_path = os.path.join(output_dir, 'best_model.pt')
        torch.save(checkpoint, best_path)
        print(f"Best model saved to {best_path}")

    return checkpoint_path


def load_checkpoint(path, model, optimizer=None, scheduler=None):
    """Load checkpoint"""

    checkpoint = torch.load(path, map_location='cpu')

    model.load_state_dict(checkpoint['model_state_dict'])

    if optimizer is not None:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    if scheduler is not None:
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

    step = checkpoint['step']
    loss = checkpoint['loss']
    perplexity = checkpoint['perplexity']

    return step, loss, perplexity


def plot_metrics(train_losses, val_losses, val_perplexities, save_path='metrics.png'):
    """Plot training metrics"""

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Loss plot
    axes[0].plot(train_losses, label='Train Loss')
    axes[0].plot(val_losses, label='Val Loss')
    axes[0].set_xlabel('Step')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)

    # Perplexity plot
    axes[1].plot(val_perplexities)
    axes[1].set_xlabel('Step')
    axes[1].set_ylabel('Perplexity')
    axes[1].set_title('Validation Perplexity')
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)