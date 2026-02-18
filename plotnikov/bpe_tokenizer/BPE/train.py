import json
import random
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple
from bpe_tokenizer import BPETokenizer
from constants import DEFAULT_TRAIN_RATIO


def load_corpus(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def split_corpus(corpus: List[str], train_ratio: float = DEFAULT_TRAIN_RATIO) -> Tuple[List[str], List[str]]:
    random.seed(42)
    random.shuffle(corpus)
    split_idx = int(len(corpus) * train_ratio)
    return corpus[:split_idx], corpus[split_idx:]


def evaluate_tokenizer(tokenizer: BPETokenizer, val_corpus: List[str]) -> dict:
    lengths = []
    reconstruction_errors = 0
    mismatched_examples = []
    
    for text in val_corpus:
        if not text.strip():
            continue
            
        try:
            ids = tokenizer.encode(text)
            reconstructed = tokenizer.decode(ids)
            
            if reconstructed != text:
                if reconstructed.strip() != text.strip():
                    reconstruction_errors += 1
                    if len(mismatched_examples) < 5:
                        mismatched_examples.append((text, reconstructed))
            
            lengths.append(len(ids))
        except Exception as e:
            print(f"Error processing text: {text[:50]}... Error: {e}")
            reconstruction_errors += 1
    
    if not lengths:
        raise ValueError("No valid texts processed for evaluation")
    
    lengths = np.array(lengths)
    
    metrics = {
        "vocab_size": tokenizer.get_vocab_size(),
        "avg_length": float(np.mean(lengths)),
        "median_length": float(np.median(lengths)),
        "max_length": int(np.max(lengths)),
        "min_length": int(np.min(lengths)),
        "p99_length": float(np.percentile(lengths, 99)),
        "reconstruction_error_rate": reconstruction_errors / len(val_corpus),
        "total_samples": len(val_corpus),
        "mismatched_examples": mismatched_examples[:5]
    }
    
    return metrics


def run_experiment(train_corpus: List[str], val_corpus: List[str], merge_configs: List[int]):
    results = {}
    
    for num_merges in merge_configs:
        print(f"\n{'='*60}")
        print(f"Training with num_merges = {num_merges}")
        print(f"{'='*60}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_corpus, num_merges=num_merges, verbose=True)
        
        save_path = f"bpe_merges_{num_merges}.json"
        tokenizer.save(save_path)
        print(f"Tokenizer saved to {save_path}")
        
        metrics = evaluate_tokenizer(tokenizer, val_corpus)
        results[num_merges] = metrics
        
        print("\nValidation Metrics:")
        for key, value in metrics.items():
            if key == "mismatched_examples":
                continue
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        if metrics["reconstruction_error_rate"] > 0:
            print(f"\n⚠️  Reconstruction errors: {metrics['reconstruction_error_rate']:.2%}")
            for orig, recon in metrics["mismatched_examples"]:
                print(f"  Original:      '{orig[:60]}...'")
                print(f"  Reconstructed: '{recon[:60]}...'")
        else:
            print("\n✅ Perfect reconstruction on validation set!")
        
        print("\nReconstruction examples:")
        for i in range(min(3, len(val_corpus))):
            text = val_corpus[i]
            ids = tokenizer.encode(text)
            reconstructed = tokenizer.decode(ids)
            status = "✓" if reconstructed == text else "✗"
            print(f"  {status} Original:      {text[:60]}...")
            print(f"    Reconstructed: {reconstructed[:60]}...")
    
    return results


def plot_results(results: dict):
    merge_values = sorted(results.keys())
    avg_lengths = [results[m]["avg_length"] for m in merge_values]
    vocab_sizes = [results[m]["vocab_size"] for m in merge_values]
    p99_lengths = [results[m]["p99_length"] for m in merge_values]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    axes[0].plot(merge_values, avg_lengths, marker='o', linewidth=2, markersize=8)
    axes[0].set_xlabel('num_merges', fontsize=12)
    axes[0].set_ylabel('Average token sequence length', fontsize=12)
    axes[0].set_title('Average Sequence Length vs num_merges', fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(merge_values, vocab_sizes, marker='o', color='green', linewidth=2, markersize=8)
    axes[1].set_xlabel('num_merges', fontsize=12)
    axes[1].set_ylabel('Vocabulary size', fontsize=12)
    axes[1].set_title('Vocabulary Size vs num_merges', fontsize=13, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(merge_values, p99_lengths, marker='o', color='red', linewidth=2, markersize=8)
    axes[2].set_xlabel('num_merges', fontsize=12)
    axes[2].set_ylabel('99th percentile length', fontsize=12)
    axes[2].set_title('P99 Sequence Length vs num_merges', fontsize=13, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('bpe_metrics.png', dpi=150, bbox_inches='tight')
    print("\n📊 Metrics plot saved to bpe_metrics.png")
    plt.show()


def main():
    DATA_PATH = "data.txt"
    MERGE_CONFIGS = [0, 2000, 8000]
    
    if not Path(DATA_PATH).exists():
        print(f"❌ Error: {DATA_PATH} not found.")
        print(f"   Please create a sample corpus file first.")
        print(f"   Example content for testing:")
        print(f"   ---")
        print(f"   This is a sample text corpus.")
        print(f"   It contains multiple lines of text.")
        print(f"   Each line is treated as a separate document.")
        print(f"   BPE tokenizer will learn subword units from this data.")
        print(f"   ---")
        return
    
    print("📂 Loading corpus...")
    corpus = load_corpus(DATA_PATH)
    print(f"✅ Loaded {len(corpus)} lines/documents")
    
    if len(corpus) < 10:
        print(f"⚠️  Warning: corpus is very small ({len(corpus)} lines).")
        print(f"   Training might not be meaningful. Consider adding more data.")
    
    train_corpus, val_corpus = split_corpus(corpus, train_ratio=DEFAULT_TRAIN_RATIO)
    print(f"✅ Train set: {len(train_corpus)} documents")
    print(f"✅ Validation set: {len(val_corpus)} documents")
    
    results = run_experiment(train_corpus, val_corpus, MERGE_CONFIGS)
    
    try:
        plot_results(results)
    except Exception as e:
        print(f"⚠️  Could not generate plot: {e}")
        print(f"   Plotting libraries might not be installed properly.")
    
    with open('experiment_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n💾 Experiment results saved to experiment_results.json")
    
    print("\n" + "="*60)
    print("🔍 Demonstration of encode/decode:")
    print("="*60)
    
    best_merges = max(MERGE_CONFIGS)
    tokenizer = BPETokenizer()
    tokenizer.load(f"bpe_merges_{best_merges}.json")
    
    test_texts = [
        "Hello world!",
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is fascinating.",
        "BPE handles rare words like supercalifragilisticexpialidocious well."
    ]
    
    for text in test_texts:
        ids = tokenizer.encode(text, add_special_tokens=True)
        reconstructed = tokenizer.decode(ids, skip_special_tokens=True)
        
        print(f"\n📝 Original:      {text}")
        print(f"🔢 Token IDs:     {ids[:20]}{'...' if len(ids) > 20 else ''} (length: {len(ids)})")
        tokens = [tokenizer.inverse_vocab.get(idx, '<UNK>') for idx in ids]
        print(f"🔤 Tokens:        {tokens[:15]}{'...' if len(tokens) > 15 else ''}")
        print(f"🔄 Reconstructed: {reconstructed}")
        print(f"✅ Match: {'YES' if reconstructed == text else 'NO'}")


if __name__ == "__main__":
    main()
