import argparse
import numpy as np
from bpe_tokenizer import BPETokenizer
from utils import load_data, split_corpus


def evaluate(model_path, data_path):
    tokenizer = BPETokenizer.load(model_path)
    lines = load_data(data_path)
    _, val = split_corpus(lines)

    lengths = []
    errors = 0

    for i, line in enumerate(val):
        ids = tokenizer.encode(line)
        decoded = tokenizer.decode(ids)
        if decoded != line:
            errors += 1
            if errors <= 3:
                print(f"ERROR line {i}: {repr(line[:60])} -> {repr(decoded[:60])}")
        lengths.append(len(ids))

    avg_len = float(np.mean(lengths))
    lengths_sorted = sorted(lengths)
    threshold = lengths_sorted[int(0.99 * len(lengths_sorted))]
    top1_pct = sum(1 for l in lengths if l > threshold) / len(lengths) * 100

    print(f"Errors:          {errors}/{len(val)}")
    print(f"Vocab size:      {len(tokenizer.vocab)}")
    print(f"Avg length:      {avg_len:.2f}")
    print(f"Top-1% threshold:{threshold}")
    print(f"Share >threshold:{top1_pct:.2f}%")


def compare_merges(data_path, merge_counts=(0, 2000, 8000)):
    lines = load_data(data_path)
    train, val = split_corpus(lines)

    print(f"{'num_merges':>12} | {'vocab_size':>10} | {'avg_len':>10}")
    print("-" * 40)

    for nm in merge_counts:
        t = BPETokenizer()
        t.train(train, num_merges=nm)
        lengths = [len(t.encode(line)) for line in val]
        print(f"{nm:>12} | {len(t.vocab):>10} | {float(np.mean(lengths)):>10.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="bpe_model.json")
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    if args.compare:
        compare_merges(args.data)
    else:
        evaluate(args.model, args.data)