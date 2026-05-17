# data.py
import torch
import numpy as np
import os
from torch.utils.data import Dataset, DataLoader
from tokenizer import BPETokenizer

class TextDataset(Dataset):
    def __init__(self, tokens, block_size):
        self.tokens = torch.tensor(tokens, dtype=torch.long)
        self.block_size = block_size
    
    def __len__(self):
        return max(0, len(self.tokens) - self.block_size)
    
    def __getitem__(self, idx):
        x = self.tokens[idx:idx + self.block_size]
        y = self.tokens[idx + 1:idx + self.block_size + 1]
        return x, y

def get_dataloaders(data_path, tokenizer_path, batch_size, block_size, val_frac=0.1, seed=1337):
    # Загрузка токенизатора
    if not os.path.exists(tokenizer_path):
        raise FileNotFoundError(f"❌ Tokenizer not found: {tokenizer_path}\n💡 Запустите: python make_tokenizer.py")
    
    tokenizer = BPETokenizer.load(tokenizer_path)
    
    # Чтение и токенизация текста
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    tokens = tokenizer.encode(text)
    
    if len(tokens) < batch_size * block_size * 2:
        print(f"❌ Not enough tokens: {len(tokens)} < {batch_size * block_size * 2}")
        print("💡 Увеличьте data.txt или уменьшите batch_size/block_size")
        return None, None, tokenizer
    
    # Split train/val
    n_val = int(len(tokens) * val_frac)
    n_val = max(n_val, block_size)  # минимум один батч для валидации
    
    train_tokens = tokens[:-n_val]
    val_tokens = tokens[-n_val:]
    
    # Datasets
    train_ds = TextDataset(train_tokens, block_size)
    val_ds = TextDataset(val_tokens, block_size)
    
    # DataLoaders
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, drop_last=True)
    
    print(f"📊 Data: train={len(train_ds)} batches, val={len(val_ds)} batches, vocab={tokenizer.vocab_len}")
    
    return train_loader, val_loader, tokenizer