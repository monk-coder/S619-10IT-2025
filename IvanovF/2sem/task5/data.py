import os
import sys
import numpy as np
import torch

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))
sys.path.insert(0, _DIR)

from bpe_tokenizer import BPETokenizer


def load_corpus(data_path, tokenizer_path):
    tok = BPETokenizer.load(tokenizer_path)

    with open(data_path, "r", encoding="utf-8") as f:
        text = f.read()

    ids = tok.encode(text)
    ids = np.array(ids, dtype=np.int32)

    n = int(len(ids) * 0.9)
    train_ids = ids[:n]
    val_ids = ids[n:]

    print(f"train tokens: {len(train_ids)}, val tokens: {len(val_ids)}, vocab: {len(tok.vocab)}")
    return train_ids, val_ids, len(tok.vocab), tok


class DataLoader:
    def __init__(self, ids, T, batch_size, device):
        self.ids = torch.tensor(ids, dtype=torch.long)
        self.T = T
        self.batch_size = batch_size
        self.device = device

        self.n_blocks = (len(ids) - 1) // T
        assert self.n_blocks >= batch_size, "corpus too small for this batch_size/T"

        x = torch.zeros(self.n_blocks, T, dtype=torch.long)
        y = torch.zeros(self.n_blocks, T, dtype=torch.long)
        for i in range(self.n_blocks):
            x[i] = self.ids[i * T: i * T + T]
            y[i] = self.ids[i * T + 1: i * T + T + 1]
        self.x = x
        self.y = y

    def get_batch(self):
        idx = torch.randint(self.n_blocks, (self.batch_size,))
        xb = self.x[idx].to(self.device)
        yb = self.y[idx].to(self.device)
        return xb, yb