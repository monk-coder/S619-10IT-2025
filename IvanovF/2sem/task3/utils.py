import random


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines


def split_corpus(lines, val_ratio=0.1, seed=42):
    random.seed(seed)
    lines = list(lines)
    random.shuffle(lines)
    split = int(len(lines) * (1 - val_ratio))
    return lines[:split], lines[split:]