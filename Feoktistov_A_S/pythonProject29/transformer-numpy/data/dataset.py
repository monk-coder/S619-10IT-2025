import numpy as np


class TextDataset:
    def __init__(self, tokens, seq_len):
        self.tokens = tokens
        self.seq_len = seq_len
        self.n_tokens = len(tokens)

    def __len__(self):
        return self.n_tokens - self.seq_len - 1

    def __getitem__(self, idx):
        x = self.tokens[idx:idx + self.seq_len]
        y = self.tokens[idx + 1:idx + self.seq_len + 1]
        return np.array(x), np.array(y)


class DataLoader:
    def __init__(self, dataset, batch_size, shuffle=True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.indices = np.arange(len(dataset))

    def __iter__(self):
        if self.shuffle:
            np.random.shuffle(self.indices)

        for i in range(0, len(self.indices), self.batch_size):
            batch_indices = self.indices[i:i + self.batch_size]
            batch_x = []
            batch_y = []

            for idx in batch_indices:
                x, y = self.dataset[idx]
                batch_x.append(x)
                batch_y.append(y)

            yield np.array(batch_x), np.array(batch_y)