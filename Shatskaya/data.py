import torch
from torch.utils.data import Dataset, DataLoader

class TextDataset(Dataset):
    def init(self, data, block_size):
        self.data = data
        self.block_size = block_size

    def len(self):
        return len(self.data) - self.block_size

    def getitem(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)


def get_dataloaders(data_path="data.txt", block_size=256, batch_size=32, train_split=0.9):
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Используем BPE токенизатор из прошлого задания
    import json
    with open("vocab.json", "r", encoding="utf-8") as f:
        vocab = json.load(f)
    
    # Простая токенизация (BPE encoding)
    tokens = []  # Здесь должна быть настоящая BPE токенизация
    for c in text:
        tokens.append(vocab.get(c, 0))  # fallback
    
    data = torch.tensor(tokens, dtype=torch.long)
    n = int(len(data) * train_split)
    
    train_ds = TextDataset(data[:n], block_size)
    val_ds = TextDataset(data[n:], block_size)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, pin_memory=True)
    
    return train_loader, val_loader, len(vocab)