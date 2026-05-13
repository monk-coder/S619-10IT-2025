"""
Упрощенный тренировочный пайплайн 
"""

import os
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
import numpy as np
from tqdm import tqdm
import time

from model import GPTLanguageModel
from data import load_data

# Параметры
batch_size = 8
block_size = 128
max_iters = 500
learning_rate = 0.001
eval_interval = 100
device = 'cpu'

print("🎯 ПРОСТОЙ ТРЕНИНГ LLM")
print("="*60)
print(f"Device: {device}")
print(f"Batch size: {batch_size}")
print(f"Max iterations: {max_iters}")
print("="*60)

# Загрузка данных
print("\n📚 Загрузка данных...")
train_loader, val_loader, tokenizer_info = load_data(
    'data.txt', block_size, batch_size, device
)

vocab_size = tokenizer_info['vocab_size']
print(f"Размер словаря: {vocab_size}")

# Создание модели
print("🏗️  Создание модели...")
model = GPTLanguageModel(
    vocab_size=vocab_size,
    n_embd=128,  # Уменьшили для скорости на CPU
    n_head=4,
    n_layer=4,
    block_size=block_size,
    dropout=0.1
).to(device)

# Подсчет параметров
total_params = sum(p.numel() for p in model.parameters())
print(f"✅ Всего параметров: {total_params:,}")

# Оптимизатор
optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

# Learning rate scheduler
scheduler = CosineAnnealingLR(optimizer, T_max=max_iters)

# Функция оценки
def estimate_loss():
    model.eval()
    losses = {'train': [], 'val': []}
    
    with torch.no_grad():
        for split, loader in [('train', train_loader), ('val', val_loader)]:
            for i, (x, y) in enumerate(loader):
                if i >= 50:  # Ограничиваем для скорости
                    break
                x, y = x.to(device), y.to(device)
                _, loss = model(x, y)
                losses[split].append(loss.item())
    
    model.train()
    return {
        'train_loss': np.mean(losses['train']),
        'val_loss': np.mean(losses['val']),
        'val_perplexity': np.exp(np.mean(losses['val']))
    }

# Создаем папку для чекпоинтов
os.makedirs('checkpoints', exist_ok=True)

# Цикл обучения
print("\n🚀 Начинаем обучение...")
print("="*60)

train_iter = iter(train_loader)
best_val_ppl = float('inf')

for iter_num in tqdm(range(max_iters), desc="Training"):
    # Получаем батч
    try:
        x, y = next(train_iter)
    except StopIteration:
        train_iter = iter(train_loader)
        x, y = next(train_iter)
    
    x, y = x.to(device), y.to(device)
    
    # Forward pass
    _, loss = model(x, y)
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    
    # Gradient clipping
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    
    optimizer.step()
    scheduler.step()
    
    # Оценка
    if iter_num % eval_interval == 0 or iter_num == max_iters - 1:
        metrics = estimate_loss()
        
        print(f"\n📊 Step {iter_num}:")
        print(f"  Train Loss: {metrics['train_loss']:.4f}")
        print(f"  Val Loss: {metrics['val_loss']:.4f}")
        print(f"  Val PPL: {metrics['val_perplexity']:.2f}")
        print(f"  LR: {scheduler.get_last_lr()[0]:.2e}")
        
        # Сохраняем лучшую модель
        if metrics['val_perplexity'] < best_val_ppl:
            best_val_ppl = metrics['val_perplexity']
            torch.save(model.state_dict(), 'checkpoints/best_model.pt')
            print(f"  ✨ Новая лучшая модель! (PPL: {best_val_ppl:.2f})")
    
    # Сохраняем чекпоинт
    if (iter_num + 1) % 500 == 0:
        torch.save(model.state_dict(), f'checkpoints/checkpoint_{iter_num+1:06d}.pt')

# Сохраняем финальную модель
torch.save(model.state_dict(), 'checkpoints/final_model.pt')

print("\n✅ Обучение завершено!")
print(f"🏆 Лучшая Perplexity: {best_val_ppl:.2f}")

# Тест генерации
print("\n🎨 Тест генерации:")
model.eval()
prompt = "Hello"
with torch.no_grad():
    # Кодируем промпт
    stoi = tokenizer_info['stoi']
    idx = torch.tensor([[stoi.get(c, 0) for c in prompt]], device=device)
    
    # Генерируем
    for _ in range(100):
        logits, _ = model(idx)
        logits = logits[0, -1, :] / 0.8
        probs = torch.softmax(logits, dim=-1)
        next_idx = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, next_idx.unsqueeze(0)), dim=1)
    
    # Декодируем
    itos = tokenizer_info['itos']
    result = ''.join([itos[int(i)] for i in idx[0]])
    print(f"Промпт: {prompt}")
    print(f"Результат: {result[:200]}...")
    # В конце train.py, после обучения, замените сохранение модели на:

# Сохраняем модель с метаданными
checkpoint = {
    'model_state_dict': model.state_dict(),
    'args': type('Args', (), {
        'n_embd': 128,
        'n_head': 4,
        'n_layer': 4,
        'block_size': block_size,
        'vocab_size': vocab_size
    })(),
    'stoi': tokenizer_info['stoi'],
    'itos': tokenizer_info['itos']
}

torch.save(checkpoint, 'checkpoints/best_model.pt')
torch.save(checkpoint, 'checkpoints/final_model.pt')

print("\n✅ Обучение завершено!")
print(f"🏆 Лучшая Perplexity: {best_val_ppl:.2f}")
