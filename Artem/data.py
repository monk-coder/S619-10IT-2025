import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from bpe_tokenizer import BPE_Tokenizer

def get_tokenizer(data_path: str = "data.txt", model_path: str = "bpe_model.json", vocab_size: int = 5000) -> BPE_Tokenizer:
    """Загружает сохранённый токенизатор или обучает новый на data.txt"""
    if os.path.exists(model_path):
        return BPE_Tokenizer.load(model_path)
    
    print(f"🔄 BPE-модель не найдена. Обучаем токенизатор на {data_path}...")
    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()
    tok = BPE_Tokenizer()
    tok.train(text, vocab_size=vocab_size)
    tok.save(model_path)
    print(f"✅ Токенизатор обучен и сохранён. Размер словаря: {tok.vocab_size}")
    return tok

class LMDataset(Dataset):
    """Датасет для языкового моделирования: возвращает (input, target) слайды"""
    def __init__(self, data: np.ndarray, block_size: int):
        self.data = data
        self.block_size = block_size

    def __len__(self):
        # Каждый блок_size-чанк становится одним примером
        return max(1, len(self.data) // self.block_size)

    def __getitem__(self, idx):
        start = idx * self.block_size
        end = start + self.block_size + 1
        chunk = self.data[start:end]
        # x = chunk[:-1], y = chunk[1:] (сдвиг на 1 токен)
        return torch.from_numpy(chunk[:-1].copy()), torch.from_numpy(chunk[1:].copy())

def load_data(data_path: str, tokenizer: BPE_Tokenizer, block_size: int, batch_size: int, split_ratio: float = 0.9):
    """Читает текст, токенизирует, разбивает на train/val и возвращает DataLoaders"""
    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Кодируем весь текст в ID
    ids = np.array(tokenizer.encode(text), dtype=np.int64)
    
    # Сплит train/val
    n = int(len(ids) * split_ratio)
    train_data, val_data = ids[:n], ids[n:]
    
    train_ds = LMDataset(train_data, block_size)
    val_ds = LMDataset(val_data, block_size)
    
    # num_workers=0 для стабильности на Windows, на Linux можно поставить 2-4
    train_dl = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        drop_last=True, num_workers=0, pin_memory=True
    )
    val_dl = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        drop_last=False, num_workers=0, pin_memory=True
    )
    return train_dl, val_dl, tokenizer