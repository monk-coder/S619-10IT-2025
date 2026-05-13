import torch
import numpy as np
import os
import json
from tqdm import tqdm


def estimate_loss(model, val_loader, eval_iters, device):
    """Оценка loss на валидации"""
    model.eval()
    losses = []

    with torch.no_grad():
        for i, (x, y) in enumerate(val_loader):
            if i >= eval_iters:
                break

            x, y = x.to(device), y.to(device)
            _, loss = model(x, y)
            losses.append(loss.item())

    model.train()
    return np.mean(losses)


def save_checkpoint(model, optimizer, scheduler, step, loss, checkpoint_dir, is_best=False):
    """Сохранение чекпоинта"""
    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint = {
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'loss': loss
    }

    # Сохраняем параметры модели (один раз)
    model_params_path = os.path.join(checkpoint_dir, 'model_params.json')
    if not os.path.exists(model_params_path):
        model_params = {
            'vocab_size': model.vocab_size,
            'embed_dim': model.embed_dim,
            'block_size': model.block_size
        }
        with open(model_params_path, 'w') as f:
            json.dump(model_params, f)

    # Обычный чекпоинт
    checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_step_{step}.pt')
    torch.save(checkpoint, checkpoint_path)

    # Лучший чекпоинт
    if is_best:
        best_path = os.path.join(checkpoint_dir, 'best_model.pt')
        torch.save(checkpoint, best_path)

    # Удаляем старые чекпоинты (оставляем последние 5)
    checkpoints = sorted([f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_step_')])
    if len(checkpoints) > 5:
        os.remove(os.path.join(checkpoint_dir, checkpoints[0]))


def load_checkpoint(model, optimizer, scheduler, checkpoint_path):
    """Загрузка чекпоинта"""
    checkpoint = torch.load(checkpoint_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    return checkpoint['step'], checkpoint['loss']


def calculate_perplexity(loss):
    """Вычисление perplexity из loss"""
    return np.exp(loss)


def get_lr_scheduler(optimizer, warmup_iters, max_iters):
    """Cosine scheduler с warmup"""

    def lr_lambda(step):
        if step < warmup_iters:
            # Линейный warmup
            return step / warmup_iters
        else:
            # Cosine decay
            progress = (step - warmup_iters) / (max_iters - warmup_iters)
            return 0.5 * (1 + np.cos(np.pi * progress))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)