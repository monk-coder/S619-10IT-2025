import numpy as np

class TextDataset:
    def __init__(self, text, tokenizer, block_size):
        self.tokenizer = tokenizer
        self.block_size = block_size
        self.tokens = tokenizer.encode(text)
        self.data = np.array(self.tokens, dtype=np.int32)

    def __len__(self):
        return max(0, len(self.data) - self.block_size)

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return x, y

class DataLoader:
    def __init__(self, dataset, batch_size, shuffle=True, seed=42):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.rng = np.random.default_rng(seed)
        self.indices = np.arange(len(dataset))

    def __iter__(self):
        if self.shuffle:
            self.rng.shuffle(self.indices)
        for i in range(0, len(self.indices), self.batch_size):
            batch_idx = self.indices[i:i + self.batch_size]
            x_batch = np.stack([self.dataset[j][0] for j in batch_idx])
            y_batch = np.stack([self.dataset[j][1] for j in batch_idx])
            yield x_batch, y_batch

    def __len__(self):
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size