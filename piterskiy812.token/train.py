#!/usr/bin/env python3
"""
Training script for BPE tokenizer.
"""

import os
import sys
import numpy as np
from bpe_tokenizer import BPETokenizer


def main():
    # Check for data file
    if not os.path.exists("data.txt"):
        print("Error: data.txt not found!")
        print("Please create data.txt with your text corpus")
        return
    
    # Read data
    with open("data.txt", "r", encoding="utf-8") as f:
        corpus = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(corpus)} lines from data.txt")
    
    if len(corpus) < 10:
        print("Warning: corpus is very small. Results may be poor.")
    
    # Split into train/val
    np.random.seed(42)
    np.random.shuffle(corpus)
    split_idx = int(len(corpus) * 0.9)
    train_corpus = corpus[:split_idx]
    val_corpus = corpus[split_idx:]
    
    print(f"Train: {len(train_corpus)} lines")
    print(f"Val: {len(val_corpus)} lines")
    
    # Train with different merge values
    merge_values = [0, 2000, 8000]
    
    for num_merges in merge_values:
        print(f"\n{'='*60}")
        print(f"Training with num_merges = {num_merges}")
        print(f"{'='*60}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_corpus, num_merges, verbose=True)
        
        # Test on validation set
        correct = 0
        total = len(val_corpus)
        
        for text in val_corpus:
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            if decoded == text:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        print(f"Decode accuracy on val set: {accuracy:.2%} ({correct}/{total})")
        
        # Save the 8000 merges model
        if num_merges == 8000:
            tokenizer.save("bpe_tokenizer_8000.json")
            print("Saved model to bpe_tokenizer_8000.json")
    
    print("\nTraining completed!")


if __name__ == "__main__":
    main()
