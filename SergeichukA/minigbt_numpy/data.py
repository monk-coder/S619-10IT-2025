# data.py
import numpy as np

class TextDataset:
    def __init__(self, text, tokenizer, block_size):
        self.tokenizer = tokenizer
        self.block_size = block_size
        
        # Токенизация всего текста
        self.tokens = tokenizer.encode(text)
        
    def __len__(self):
        return max(0, len(self.tokens) - self.block_size)
    
    def __getitem__(self, idx):
        """Возвращает пару (context, next_token)"""
        chunk = self.tokens[idx:idx + self.block_size + 1]
        x = np.array(chunk[:-1], dtype=np.int32)
        y = np.array(chunk[1:], dtype=np.int32)
        return x, y
    
    def get_batch(self, indices, batch_size):
        """Формирует батч"""
        X, Y = [], []
        for idx in indices:
            x, y = self[idx]
            X.append(x)
            Y.append(y)
        return np.stack(X), np.stack(Y)