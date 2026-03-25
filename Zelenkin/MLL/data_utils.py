import numpy as np
from tqdm import tqdm


class DataLoader:
    def __init__(self, tokens, block_size, batch_size, train_split=0.9):
        self.tokens = tokens
        self.block_size = block_size
        self.batch_size = batch_size

        # Разделение на train/val
        split_idx = int(len(tokens) * train_split)
        self.train_tokens = tokens[:split_idx]
        self.val_tokens = tokens[split_idx:]

        self.train_pos = 0
        self.val_pos = 0

    def get_batch(self, split='train'):
        if split == 'train':
            tokens = self.train_tokens
            pos = self.train_pos
        else:
            tokens = self.val_tokens
            pos = self.val_pos

        # Случайные батчи
        idx = np.random.randint(0, len(tokens) - self.block_size - 1, self.batch_size)
        x = np.array([tokens[i:i + self.block_size] for i in idx])
        y = np.array([tokens[i + 1:i + self.block_size + 1] for i in idx])

        return x, y


def load_data(file_path, tokenizer):
    """Загрузка и токенизация данных"""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Токенизация
    tokens = tokenizer.encode(text)
    return tokens


def create_dataloader(tokens, block_size, batch_size, train_split=0.9):
    """Создание даталоадера"""
    return DataLoader(tokens, block_size, batch_size, train_split)