"""
DataLoader для языковой модели
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

class TextDataset(Dataset):
    """Датасет для языковой модели"""
    
    def __init__(self, data, block_size):
        self.data = torch.tensor(data, dtype=torch.long)
        self.block_size = block_size
        
    def __len__(self):
        return len(self.data) - self.block_size
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return x, y

def load_data(data_path, block_size, batch_size, device, train_split=0.9):
    """
    Загрузка данных и создание DataLoader'ов
    """
    print(f"📖 Загрузка данных из {data_path}...")
    
    # Читаем текст
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Проверяем, не пустой ли файл
    if len(text) < 100:
        print("⚠️ Файл слишком маленький, добавляем тестовые данные...")
        text = text + " " + "This is additional training data. " * 100
    
    # Создаем простой character-level токенизатор
    chars = sorted(list(set(text)))
    vocab_size = len(chars)
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    
    print(f"📊 Размер словаря: {vocab_size} символов")
    print(f"📊 Длина текста: {len(text)} символов")
    
    # Преобразуем текст в токены
    data = [stoi[ch] for ch in text]
    
    # Проверяем диапазон токенов
    print(f"📊 Диапазон токенов: {min(data)} - {max(data)}")
    
    # Разделяем на train/val
    n = len(data)
    train_data = data[:int(n * train_split)]
    val_data = data[int(n * train_split):]
    
    print(f"📊 Train примеров: {len(train_data)}")
    print(f"📊 Val примеров: {len(val_data)}")
    
    # Создаем датасеты
    train_dataset = TextDataset(train_data, block_size)
    val_dataset = TextDataset(val_data, block_size)
    
    # Создаем DataLoader'ы
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )
    
    tokenizer_info = {
        'vocab_size': vocab_size,
        'stoi': stoi,
        'itos': itos
    }
    
    return train_loader, val_loader, tokenizer_info