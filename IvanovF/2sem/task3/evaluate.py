import numpy as np
from bpe_tokenizer import BPETokenizer
from utils import load_data, split_corpus


def evaluate(model_path, data_path):
    tokenizer = BPETokenizer.load(model_path)

    lines = load_data(data_path)
    train, val = split_corpus(lines)

    lengths = []
    for line in val:
        ids = tokenizer.encode(line)
        decoded = tokenizer.decode(ids)

        assert decoded == line

        lengths.append(len(ids))

    avg_len = np.mean(lengths)
    vocab_size = len(tokenizer.vocab)

    lengths_sorted = sorted(lengths)
    threshold = lengths_sorted[int(0.99 * len(lengths))]

    print("Vocab size:", vocab_size)
    print("Average length:", avg_len)
    print("Top 1% length threshold:", threshold)


if __name__ == "__main__":
    evaluate("bpe_model.json", "data.txt")
