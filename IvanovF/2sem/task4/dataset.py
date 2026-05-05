import numpy as np
import sys
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))
from bpe_tokenizer import BPETokenizer
from utils import load_data, split_corpus


def build_dataset(data_path, tokenizer_path, T):
    lines = load_data(data_path)
    train_lines, val_lines = split_corpus(lines)

    tokenizer = BPETokenizer.load(tokenizer_path)

    def encode_corpus(lines):
        ids = []
        for line in lines:
            ids.extend(tokenizer.encode(line))
        return np.array(ids, dtype=np.int32)

    train_ids = encode_corpus(train_lines)
    val_ids = encode_corpus(val_lines)

    def make_batches(ids, T):
        n = (len(ids) - 1) // T
        x = np.zeros((n, T), dtype=np.int32)
        y = np.zeros((n, T), dtype=np.int32)
        for i in range(n):
            x[i] = ids[i * T: i * T + T]
            y[i] = ids[i * T + 1: i * T + T + 1]
        return x, y

    x_train, y_train = make_batches(train_ids, T)
    x_val, y_val = make_batches(val_ids, T)

    return x_train, y_train, x_val, y_val, tokenizer