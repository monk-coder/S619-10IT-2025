#!/usr/bin/env python3
"""
Train BPE Tokenizer on data.txt
"""

import os
from bpe_tokenizer import BPETokenizer

def load_data(filepath):
    """Load corpus from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    print("BPE Tokenizer Training")
    print("=" * 40)
    
    # Путь к данным
    data_path = "0/data.txt"
    
    # Check data file
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found!")
        print("Current directory:", os.getcwd())
        print("Available files:")
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".txt"):
                    print(f"  {os.path.join(root, file)}")
        return
    
    # Load data
    corpus = load_data(data_path)
    print(f"Loaded {len(corpus)} lines from {data_path}")
    
    if len(corpus) < 10:
        print("Warning: Small dataset")
    
    # Split train/val
    split_idx = int(len(corpus) * 0.9)
    train = corpus[:split_idx]
    val = corpus[split_idx:split_idx + 10]
    
    print(f"Training on {len(train)} lines")
    print(f"Testing on {len(val)} lines")
    
    # Train with required merges: 0, 2000, 8000
    merge_values = [0, 2000, 8000]
    
    for merges in merge_values:
        print(f"\nTraining with {merges} merges...")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train, merges, verbose=True)
        
        # Test encode/decode
        correct = 0
        for text in val:
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            if decoded == text:
                correct += 1
        
        accuracy = correct / len(val) * 100 if len(val) > 0 else 0
        print(f"Decode accuracy: {accuracy:.1f}% ({correct}/{len(val)})")
        
        # Save final model
        if merges == 8000:
            tokenizer.save("bpe_tokenizer_8000.json")
            print("Saved: bpe_tokenizer_8000.json")
    
    print("\n✅ Training complete!")

if __name__ == "__main__":
    main()
