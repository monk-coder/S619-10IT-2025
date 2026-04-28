import torch
from torch.utils.data import Dataset, DataLoader
import json
import os

class BPETokenizer:
    """Загрузчик токенизатора из JSON (совместим с Заданием 3/4)"""
    def __init__(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.token_to_id = data['token_to_id']
        self.id_to_token = data['id_to_token']
        self.vocab_size = data['vocab_size']

    def encode(self, text):
        # Простой char-level fallback. Если нужен полный BPE, замени на свой encode()
        return [self.token_to_id.get(c, 0) for c in text.lower()]

    def decode(self, ids):
        return ''.join(self.id_to_token.get(i, '<unk>') for i in ids)

class TextDataset(Dataset):
    def __init__(self, text, tokenizer, block_size=128):
        self.data = torch.tensor(tokenizer.encode(text), dtype=torch.long)
        self.block_size = block_size

    def __len__(self):
        return max(0, len(self.data) - self.block_size)

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return x, y

def get_dataloaders(data_path, tokenizer_path, block_size=128, batch_size=64, val_split=0.1):
    tokenizer = BPETokenizer(tokenizer_path)
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    split_idx = int(len(text) * (1 - val_split))
    train_ds = TextDataset(text[:split_idx], tokenizer, block_size)
    val_ds = TextDataset(text[split_idx:], tokenizer, block_size)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, drop_last=True)
    return train_loader, val_loader, tokenizer