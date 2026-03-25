# data.py
import torch
import pickle
import os
import sys
from torch.utils.data import Dataset, DataLoader as TorchDataLoader

# Импортируем класс токенизатора
try:
    from tokenizer_class import FreshTokenizer
except ImportError:
    # Если файла нет, определяем класс здесь
    class FreshTokenizer:
        def __init__(self):
            self.vocab_size = 0
            self.char_to_idx = {}
            self.idx_to_char = {}

        def encode(self, text):
            return [self.char_to_idx.get(ch, 0) for ch in text]

        def decode(self, tokens):
            return ''.join([self.idx_to_char.get(t, '?') for t in tokens])


class TextDataset(Dataset):
    def __init__(self, tokens, seq_len):
        self.tokens = tokens
        self.seq_len = seq_len
        self.n_samples = len(tokens) - seq_len - 1

    def __len__(self):
        return max(0, self.n_samples)

    def __getitem__(self, idx):
        x = self.tokens[idx:idx + self.seq_len]
        y = self.tokens[idx + 1:idx + self.seq_len + 1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)


def load_tokenizer(tokenizer_path='tokenizer.pkl'):
    """Загружает токенизатор"""

    if not os.path.exists(tokenizer_path):
        print(f"❌ Файл {tokenizer_path} не найден!")
        sys.exit(1)

    if os.path.isdir(tokenizer_path):
        print(f"❌ {tokenizer_path} - это папка, а не файл!")
        sys.exit(1)

    size = os.path.getsize(tokenizer_path)
    if size == 0:
        print(f"❌ Файл {tokenizer_path} пустой!")
        sys.exit(1)

    print(f"Файл токенизатора: {size} байт")

    try:
        with open(tokenizer_path, 'rb') as f:
            tokenizer = pickle.load(f)

        print(f"✅ Токенизатор загружен")
        print(f"   vocab_size: {tokenizer.vocab_size}")
        return tokenizer

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        sys.exit(1)


def load_data(data_path='data.txt', tokenizer_path='tokenizer.pkl', train_split=0.9):
    """Load and tokenize data"""

    print("\n" + "=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    tokenizer = load_tokenizer(tokenizer_path)

    if not os.path.exists(data_path):
        print(f"❌ Файл {data_path} не найден!")
        sys.exit(1)

    print(f"\nЗагрузка текста из {data_path}...")
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Загружено {len(text)} символов")

    print("Токенизация текста...")
    tokens = tokenizer.encode(text)

    print(f"Получено {len(tokens)} токенов")

    split_idx = int(len(tokens) * train_split)
    train_tokens = tokens[:split_idx]
    val_tokens = tokens[split_idx:]

    print(f"Обучающая выборка: {len(train_tokens)} токенов")
    print(f"Валидационная выборка: {len(val_tokens)} токенов")

    return train_tokens, val_tokens, tokenizer


def create_dataloaders(train_tokens, val_tokens, seq_len, batch_size, device='cuda'):
    """Create dataloaders"""

    train_dataset = TextDataset(train_tokens, seq_len)
    val_dataset = TextDataset(val_tokens, seq_len)

    train_loader = TorchDataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=True if device == 'cuda' else False
    )

    val_loader = TorchDataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True if device == 'cuda' else False
    )

    return train_loader, val_loader