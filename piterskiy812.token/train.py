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
    
    # ПУТЬ К ДАННЫМ - читаем из папки 0
    data_path = "../0/data.txt"
    
    # Check data file
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found!")
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
        print(f"\n{'='*50}")
        print(f"Training with {merges} merges...")
        print(f"{'='*50}")
        
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
            print("✅ Model saved: bpe_tokenizer_8000.json")
    
    # Финальная проверка - загружаем сохраненную модель и смотрим размер
    if os.path.exists("bpe_tokenizer_8000.json"):
        print(f"\n{'='*50}")
        print("Loading saved model for final check...")
        loaded = BPETokenizer()
        loaded.load("bpe_tokenizer_8000.json")
        print(f"✅ Final vocabulary size: {len(loaded.vocab)} tokens")
        print(f"✅ Merges performed: {len(loaded.merges)}")
    
    print(f"\n{'='*50}")
    print("✅ Training complete!")

if __name__ == "__main__":
    main()
