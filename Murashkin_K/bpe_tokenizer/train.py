import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import json
import os
from bpe_tokenizer import BPETokenizer, split_corpus


def evaluate(tokenizer: BPETokenizer, val_corpus: list, n_samples: int = 500) -> dict:
    lengths = []
    perfect = 0
    total = 0

    for text in tqdm(val_corpus[:n_samples], desc="Eval"):
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)

        lengths.append(len(ids))
        if decoded == text:
            perfect += 1
        total += 1

    avg_len = np.mean(lengths)
    p99 = np.percentile(lengths, 99)
    long_ratio = sum(1 for l in lengths if l > p99) / len(lengths)

    return {
        'vocab_size': tokenizer.vocab_size,
        'avg_length': float(avg_len),
        'p99_length': float(p99),
        'long_ratio': float(long_ratio),
        'perfect_rate': perfect / total
    }


def run_experiment():
    print("🚀 === BPE ТОКЕНИЗАТОР ===\n")

    train_corpus, val_corpus = split_corpus('data/data.txt')
    print(f"📚 Train: {len(train_corpus):,} | Val: {len(val_corpus):,}")

    experiments = [0, 2000, 8000]
    results = {}

    for num_merges in experiments:
        print(f"\n🔬 num_merges = {num_merges:,}")
        tokenizer = BPETokenizer()
        tokenizer.train(train_corpus, num_merges)
        metrics = evaluate(tokenizer, val_corpus)
        results[num_merges] = metrics
        tokenizer.save(f'bpe_model_{num_merges}.json')

    json.dump(results, open('results.json', 'w'), indent=2, ensure_ascii=False)
    plot_experiment(results, experiments)
    print_table(results)

    demo('bpe_model_8000.json')


def plot_experiment(results, experiments):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x = experiments
    avg_lens = [results[m]['avg_length'] for m in x]
    perfects = [results[m]['perfect_rate'] for m in x]

    ax1.plot(x, avg_lens, 'o-', linewidth=3, markersize=8)
    ax1.set_title('Средняя длина токенов')
    ax1.set_xlabel('num_merges')
    ax1.grid(True, alpha=0.3)

    ax2.plot(x, perfects, 's-', linewidth=3, markersize=8, color='orange')
    ax2.set_title('Точность восстановления')
    ax2.set_xlabel('num_merges')
    ax2.set_ylabel('decode(encode()) == text')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('bpe_results.png', dpi=300, bbox_inches='tight')
    plt.show()


def print_table(results):
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("| num_merges | словарь | средняя_длина | длинные(1%) | точность |")
    print("-" * 70)
    for m in sorted(results):
        r = results[m]
        print(f"| {m:>9,} | {r['vocab_size']:>7,} | "
              f"{r['avg_length']:>11.1f} | "
              f"{r['long_ratio'] * 100:>9.1f}% | "
              f"{r['perfect_rate']:>8.1%} |")


def demo(model_path):
    tokenizer = BPETokenizer.load(model_path)
    texts = ["Привет, мир!", "Machine Learning BPE", "reverse engineering"]

    print("\n🎯 ДЕМО:")
    for text in texts:
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)
        print(f"'{text}' → {len(ids)} токенов → '{decoded}' "
              f"{'✓' if decoded == text else '✗'}")


if __name__ == "__main__":
    run_experiment()
