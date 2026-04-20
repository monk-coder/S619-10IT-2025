import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
import os


class CharDataset(Dataset):
    def __init__(self, data, block_size):
        self.data = data
        self.block_size = block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)


def load_data(data_path, vocab_size, block_size, batch_size, device='cpu'):
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

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0,
                              pin_memory=(device == 'cuda'))
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0,
                            pin_memory=(device == 'cuda'))

    return train_loader, val_loader, len(chars), stoi, itos


def get_batch(loader):
    for x, y in loader:
        yield x, y