import numpy as np
from typing import List, Tuple
from bpe_tokenizer import BPETokenizer


def load_data(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def train_tokenizer(text: str, vocab_size: int = 1000, save_path: str = 'tokenizer.json') -> BPETokenizer:
    """Обучает BPE токенизатор на тексте (весь текст как единый блок)"""
    tokenizer = BPETokenizer()
    # Важно: передаём весь текст как один элемент списка, чтобы все символы попали в vocab
    tokenizer.train([text], num_merges=vocab_size)
    tokenizer.save(save_path)
    print(f"Tokenizer trained: {len(tokenizer)} tokens")
    return tokenizer


def load_tokenizer(path: str = 'tokenizer.json') -> BPETokenizer:
    """Загружает сохранённый токенизатор"""
    return BPETokenizer.load(path)


class TokenDataset:
    def __init__(self, tokens: np.ndarray, seq_len: int = 128):
        self.seq_len = seq_len
        self.tokens = tokens.astype(np.int32)
        self.n_samples = max(0, len(self.tokens) - seq_len)
        
    def __len__(self):
        return self.n_samples
    
    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray]:
        x = self.tokens[idx:idx+self.seq_len]
        y = self.tokens[idx+1:idx+self.seq_len+1]
        return x, y


def get_dataloader(dataset: TokenDataset, batch_size: int, shuffle: bool = True):
    indices = np.arange(len(dataset))
    if shuffle:
        np.random.shuffle(indices)
    for start in range(0, len(indices), batch_size):
        batch_idx = indices[start:start+batch_size]
        if len(batch_idx) < batch_size:
            continue
        xs = np.stack([dataset[i][0] for i in batch_idx])
        ys = np.stack([dataset[i][1] for i in batch_idx])
        yield xs, ys