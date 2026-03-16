import json
import random
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple
from bpe_tokenizer import BPETokenizer


def load_corpus(path: str) -> List[str]:
    """Load corpus from UTF-8 text file."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Split into lines/documents
    documents = [line.strip() for line in text.splitlines() if line.strip()]
    return documents


def split_corpus(corpus: List[str], train_ratio: float = 0.9) -> Tuple[List[str], List[str]]:
    """Split corpus into train and validation sets."""
    random.seed(42)
    random.shuffle(corpus)
    split_idx = int(len(corpus) * train_ratio)
    return corpus[:split_idx], corpus[split_idx:]


def evaluate_tokenizer(tokenizer: BPETokenizer, val_corpus: List[str]) -> dict:
    """Evaluate tokenizer on validation set."""
    lengths = []
    reconstruction_errors = 0
    
    for text in val_corpus:
        ids = tokenizer.encode(text)
        reconstructed = tokenizer.decode(ids)
        lengths.append(len(ids))
        
        if reconstructed != text:
            reconstruction_errors += 1
    
    lengths = np.array(lengths)
    top_1_percent_threshold = np.percentile(lengths, 99)
    long_sequences_ratio = np.mean(lengths > top_1_percent_threshold)
    
    return {
        "vocab_size": tokenizer.vocab_size(),
        "avg_length": float(np.mean(lengths)),
        "median_length": float(np.median(lengths)),
        "max_length": int(np.max(lengths)),
        "top_1_percent_threshold": int(top_1_percent_threshold),
        "long_sequences_ratio": float(long_sequences_ratio),
        "reconstruction_errors": reconstruction_errors,
        "total_samples": len(val_corpus)
    }


def run_experiment(train_corpus: List[str], val_corpus: List[str], merge_configs: List[int]):
    """Run experiment with different num_merges values."""
    results = []
    
    for num_merges in merge_configs:
        print(f"\n{'='*60}")
        print(f"Training with num_merges = {num_merges}")
        print(f"{'='*60}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_corpus, num_merges=num_merges, verbose=True)
        
        # Save merges and vocab
        merges_path = f"merges_{num_merges}.json"
        vocab_path = f"vocab_{num_merges}.json"
        tokenizer.save(merges_path)
        
        # Save vocab separately for inspection
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(tokenizer.vocab, f, ensure_ascii=False, indent=2)
        
        # Evaluate
        metrics = evaluate_tokenizer(tokenizer, val_corpus)
        metrics["num_merges"] = num_merges
        results.append(metrics)
        
        print(f"\nResults for num_merges={num_merges}:")
        print(f"  Vocabulary size: {metrics['vocab_size']}")
        print(f"  Avg tokens per doc: {metrics['avg_length']:.2f}")
        print(f"  Reconstruction errors: {metrics['reconstruction_errors']}/{metrics['total_samples']}")
    
    # Plot results
    plot_results(results)
    return results


def plot_results(results: list):
    """Plot avg length vs num_merges."""
    merges = [r["num_merges"] for r in results]
    avg_lengths = [r["avg_length"] for r in results]
    vocab_sizes = [r["vocab_size"] for r in results]
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    color = 'tab:blue'
    ax1.set_xlabel('Number of Merges')
    ax1.set_ylabel('Avg Tokens per Document', color=color)
    ax1.plot(merges, avg_lengths, 'o-', color=color, linewidth=2, markersize=8)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Vocabulary Size', color=color)
    ax2.plot(merges, vocab_sizes, 's--', color=color, linewidth=2, markersize=8)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('BPE: Effect of num_merges on Tokenization')
    plt.tight_layout()
    plt.savefig('bpe_experiment.png', dpi=150)
    print("\nPlot saved as 'bpe_experiment.png'")


def demo_tokenizer(tokenizer: BPETokenizer):
    """Demonstrate encode/decode functionality."""
    examples = [
        "Hello world!",
        "The quick brown fox jumps over the lazy dog.",
        "Привет мир! 123",
        "Tokenization is fun 😊",
        "   multiple   spaces   "
    ]
    
    print("\n" + "="*60)
    print("DEMONSTRATION: encode/decode examples")
    print("="*60)
    
    for text in examples:
        ids = tokenizer.encode(text)
        reconstructed = tokenizer.decode(ids)
        status = "✓" if text == reconstructed else "✗"
        print(f"\n{status} Original:  {repr(text)}")
        print(f"  Encoded:    {ids[:20]}{'...' if len(ids) > 20 else ''} (len={len(ids)})")
        print(f"  Decoded:    {repr(reconstructed)}")
        if text != reconstructed:
            print(f"  ERROR: Mismatch!")


def main():
    # Configuration
    DATA_PATH = "data.txt"
    MERGE_CONFIGS = [0, 2000, 8000]  # Experiment values
    
    # Check if data exists
    if not Path(DATA_PATH).exists():
        print(f"Error: {DATA_PATH} not found. Please place your corpus file in this directory.")
        return
    
    # Load and split corpus
    print("Loading corpus...")
    corpus = load_corpus(DATA_PATH)
    print(f"Loaded {len(corpus)} documents")
    
    train_corpus, val_corpus = split_corpus(corpus, train_ratio=0.9)
    print(f"Train: {len(train_corpus)} docs, Val: {len(val_corpus)} docs")
    
    # Save splits for reproducibility
    with open('train_docs.json', 'w', encoding='utf-8') as f:
        json.dump(train_corpus[:100], f, ensure_ascii=False, indent=2)  # save subset
    with open('val_docs.json', 'w', encoding='utf-8') as f:
        json.dump(val_corpus[:100], f, ensure_ascii=False, indent=2)
    
    # Run experiment
    results = run_experiment(train_corpus, val_corpus, MERGE_CONFIGS)
    
    # Save final results
    with open('experiment_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nExperiment results saved to 'experiment_results.json'")
    
    # Demo with best model (largest num_merges)
    best_merges = max(MERGE_CONFIGS)
    print(f"\nLoading best model (num_merges={best_merges}) for demonstration...")
    tokenizer = BPETokenizer.load(f"merges_{best_merges}.json")
    demo_tokenizer(tokenizer)
    
    # Final validation check
    print("\n" + "="*60)
    print("FINAL VALIDATION: decode(encode(x)) == x")
    print("="*60)
    errors = 0
    for i, text in enumerate(val_corpus[:1000]):  # check first 1000 validation docs
        if tokenizer.decode(tokenizer.encode(text)) != text:
            errors += 1
            if errors <= 5:  # show first 5 errors
                print(f"Error on doc {i}: {repr(text[:50])}...")
    
    if errors == 0:
        print(f"✓ All {min(1000, len(val_corpus))} validation documents reconstructed perfectly!")
    else:
        print(f"✗ {errors} reconstruction errors found")


if __name__ == "__main__":
    main()