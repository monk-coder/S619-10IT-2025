import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
import os


class BPEEncoder:
    """Простой BPE-подобный энкодер для совместимости с заданием 3"""

    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.merges = {}

    def train(self, text):
        """Обучение BPE (упрощенная версия)"""
        # Создаем словарь из символов
        chars = sorted(list(set(text)))
        self.vocab_size = min(self.vocab_size, len(chars))

        # Базовый словарь
        for i, char in enumerate(chars[:self.vocab_size]):
            self.char_to_idx[char] = i
            self.idx_to_char[i] = char

    def encode(self, text):
        """Кодирование текста в индексы"""
        return [self.char_to_idx.get(c, 0) for c in text]

    def decode(self, indices):
        """Декодирование индексов в текст"""
        return ''.join([self.idx_to_char.get(i, '') for i in indices])

    def save(self, path):
        """Сохранение энкодера"""
        torch.save({
            'char_to_idx': self.char_to_idx,
            'idx_to_char': self.idx_to_char,
            'vocab_size': self.vocab_size
        }, path)

    def load(self, path):
        """Загрузка энкодера"""
        data = torch.load(path)
        self.char_to_idx = data['char_to_idx']
        self.idx_to_char = data['idx_to_char']
        self.vocab_size = data['vocab_size']


class TextDataset(Dataset):
    """Датасет для текстовых данных"""

    def __init__(self, text, encoder, block_size):
        self.encoder = encoder
        self.block_size = block_size
        self.data = torch.tensor(encoder.encode(text), dtype=torch.long)

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return x, y


def load_data(data_path, encoder, block_size, batch_size, device='cpu'):
    """Загрузка и подготовка данных"""
    # Читаем файл
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Разделяем на train/val (90/10)
    split_idx = int(0.9 * len(text))
    train_text = text[:split_idx]
    val_text = text[split_idx:]

    # Создаем датасеты
    train_dataset = TextDataset(train_text, encoder, block_size)
    val_dataset = TextDataset(val_text, encoder, block_size)

    # Создаем даталоадеры
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=True if device == 'cuda' else False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True if device == 'cuda' else False
    )

    return train_loader, val_loader, len(encoder.char_to_idx)