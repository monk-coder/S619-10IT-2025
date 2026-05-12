import torch
from torch.utils.data import Dataset, DataLoader
import pickle
import os

class TokenDataset(Dataset):
    def __init__(self, tokens, block_size):
        self.tokens = tokens
        self.block_size = block_size
        self.length = max(0, len(tokens) - block_size)

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        chunk = self.tokens[idx:idx + self.block_size + 1]
        return torch.tensor(chunk[:-1], dtype=torch.long), torch.tensor(chunk[1:], dtype=torch.long)

def get_dataloaders(data_path, tokenizer_path, batch_size, block_size, seed=1337, val_frac=0.1):
    if os.path.exists(tokenizer_path):
        with open(tokenizer_path, 'rb') as f:
            tokenizer = pickle.load(f)
    else:
        raise FileNotFoundError(f"Tokenizer not found at {tokenizer_path}")

    text = open(data_path, 'r', encoding='utf-8').read()
    tokens = tokenizer.encode(text)
    print(f"📊 Total tokens: {len(tokens)} | Block size: {block_size}")

    # Адаптивный split: гарантируем, что val содержит минимум block_size+5 токенов
    n = len(tokens)
    val_size = max(block_size + 5, int(n * val_frac))
    if val_size >= n - 1:
        val_size = n // 2  # fallback для микроскопических датасетов
        
    train_tokens = tokens[:n - val_size]
    val_tokens = tokens[n - val_size:]

    train_ds = TokenDataset(train_tokens, block_size)
    val_ds = TokenDataset(val_tokens, block_size)

    g = torch.Generator()
    g.manual_seed(seed)

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=g, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0) if len(val_ds) > 0 else None

    return train_dl, val_dl, tokenizer