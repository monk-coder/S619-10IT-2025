#!/usr/bin/env python3
"""
BPE Tokenizer Training Script
Trains BPE tokenizer with different numbers of merges and evaluates metrics.
"""

import os
import sys
import json
import numpy as np
from bpe_tokenizer import BPETokenizer, split_train_val, calculate_metrics, validate_decoding


def load_corpus(filepath: str) -> List[str]:
    """Load corpus from file.
    
    Args:
        filepath: Path to corpus file
        
    Returns:
        List of text lines
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def run_experiment(train_corpus: List[str], val_corpus: List[str], 
                   merge_values: List[int]) -> List[Dict]:
    """Run experiment with different merge values.
    
    Args:
        train_corpus: Training corpus
        val_corpus: Validation corpus
        merge_values: List of num_merges values
        
    Returns:
        List of experiment results
    """
    results = []
    
    for num_merges in merge_values:
        print(f"\n{'='*60}")
        print(f"Experiment with num_merges = {num_merges}")
        print(f"{'='*60}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_corpus, num_merges, verbose=True)
        
        metrics = calculate_metrics(tokenizer, val_corpus)
        
        decode_test = validate_decoding(tokenizer, val_corpus, num_samples=50)
        metrics['decode_test_passed'] = decode_test
        
        results.append({
            'num_merges': num_merges,
            'metrics': metrics,
            'tokenizer': tokenizer
        })
        
        print(f"\nMetrics for num_merges={num_merges}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        if decode_test:
            print("  ✓ Decoding test PASSED")
        else:
            print("  ✗ Decoding test FAILED")
    
    return results


def save_experiment_results(results: List[Dict], output_dir: str = "."):
    """Save experiment results to JSON file.
    
    Args:
        results: Experiment results
        output_dir: Output directory
    """
    exp_results = []
    for res in results:
        exp_results.append({
            'num_merges': res['num_merges'],
            'metrics': res['metrics']
        })
    
    output_path = os.path.join(output_dir, "experiment_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exp_results, f, ensure_ascii=False, indent=2)
    print(f"\nExperiment results saved to {output_path}")


def save_splits(train_corpus: List[str], val_corpus: List[str], output_dir: str = "data"):
    """Save train/val splits to files.
    
    Args:
        train_corpus: Training corpus
        val_corpus: Validation corpus
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    train_path = os.path.join(output_dir, "train.txt")
    val_path = os.path.join(output_dir, "val.txt")
    
    with open(train_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(train_corpus))
    
    with open(val_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(val_corpus))
    
    print(f"Train split saved to {train_path} ({len(train_corpus)} lines)")
    print(f"Val split saved to {val_path} ({len(val_corpus)} lines)")


def plot_results(results: List[Dict], output_dir: str = "."):
    """Plot experiment results.
    
    Args:
        results: Experiment results
        output_dir: Output directory
    """
    try:
        import matplotlib.pyplot as plt
        
        merges = [r['num_merges'] for r in results]
        avg_lengths = [r['metrics']['avg_length'] for r in results]
        vocab_sizes = [r['metrics']['vocab_size'] for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Average length vs merges
        ax1.plot(merges, avg_lengths, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Number of Merges')
        ax1.set_ylabel('Average Sequence Length (tokens)')
        ax1.set_title('Sequence Length vs BPE Merges')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Vocabulary size vs merges
        ax2.plot(merges, vocab_sizes, 'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Number of Merges')
        ax2.set_ylabel('Vocabulary Size')
        ax2.set_title('Vocabulary Size vs BPE Merges')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, "bpe_length_vs_merges.png")
        plt.savefig(output_path, dpi=150)
        plt.show()
        print(f"Plot saved to {output_path}")
        
    except ImportError:
        print("\nMatplotlib not available, skipping plots")


def demonstrate_tokenizer(tokenizer: BPETokenizer):
    """Demonstrate tokenizer functionality.
    
    Args:
        tokenizer: Trained tokenizer
    """
    print("\n" + "="*60)
    print("Tokenizer Demonstration")
    print("="*60)
    
    test_texts = [
        "Hello, world!",
        "Привет, мир!",
        "This is a test sentence for BPE tokenizer.",
        "123 + 456 = 579",
        "Emoji test: 😊🎉🚀"
    ]
    
    for text in test_texts:
        print(f"\nText: '{text}'")
        ids = tokenizer.encode(text)
        print(f"Encoded IDs: {ids}")
        print(f"Number of tokens: {len(ids)}")
        decoded = tokenizer.decode(ids)
        print(f"Decoded: '{decoded}'")
        print(f"Match: {decoded == text}")
    
    print(f"\nVocabulary size: {tokenizer.vocab_size}")
    print(f"Number of merges: {len(tokenizer.merges)}")
    
    # Show some vocabulary items
    print("\nSample vocabulary items (first 20):")
    vocab_items = list(tokenizer.vocab.items())
    for token, id_ in vocab_items[:20]:
        print(f"  ID {id_:4d}: '{repr(token)}'")


def main():
    """Main training script."""
    # Check for data file
    data_file = "data.txt"
    if not os.path.exists(data_file):
        print(f"Error: File {data_file} not found!")
        print("Please place your text corpus in data.txt (UTF-8 encoding)")
        sys.exit(1)
    
    # Load corpus
    print(f"Loading corpus from {data_file}...")
    corpus = load_corpus(data_file)
    print(f"Loaded {len(corpus)} lines")
    
    # Split train/val
    print("\nSplitting into train/val sets (90/10)...")
    train_corpus, val_corpus = split_train_val(corpus, val_ratio=0.1)
    save_splits(train_corpus, val_corpus)
    
    # Experiment with different merge values
    merge_values = [0, 2000, 8000]  # As specified in the task
    
    print("\n" + "="*60)
    print("Running BPE experiments")
    print("="*60)
    
    results = run_experiment(train_corpus, val_corpus, merge_values)
    
    # Save results
    save_experiment_results(results)
    
    # Plot results
    plot_results(results)
    
    # Train final tokenizer with best parameters (8000 merges)
    print("\n" + "="*60)
    print("Training final tokenizer (num_merges=8000)")
    print("="*60)
    
    final_tokenizer = BPETokenizer()
    final_tokenizer.train(train_corpus, num_merges=8000, verbose=True)
    
    # Save final tokenizer
    final_tokenizer.save("bpe_tokenizer_8000.json")
    
    # Save merge rules separately
    with open("bpe_merges.json", 'w', encoding='utf-8') as f:
        json.dump(final_tokenizer.merges, f, ensure_ascii=False, indent=2)
    print("Merge rules saved to bpe_merges.json")
    
    # Demonstrate final tokenizer
    demonstrate_tokenizer(final_tokenizer)
    
    # Final validation
    print("\n" + "="*60)
    print("Final validation on val corpus")
    print("="*60)
    
    all_passed = validate_decoding(final_tokenizer, val_corpus, num_samples=100)
    if all_passed:
        print("✓ All validation samples passed decode(encode(text)) == text")
    else:
        print("✗ Some validation samples failed")
    
    final_metrics = calculate_metrics(final_tokenizer, val_corpus)
    
    print("\nFinal metrics:")
    for key, value in final_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Training completed successfully!")
    print("="*60)


if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Add type hints
    from typing import List, Dict
    
    main()
