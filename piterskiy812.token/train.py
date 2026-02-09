import os
import json
import random
from bpe_tokenizer import BPETokenizer


def load_corpus(filepath: str):
    """Load corpus from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def main():
    # Check if data.txt exists
    if not os.path.exists("data.txt"):
        print("Error: data.txt not found!")
        print("Please make sure data.txt is in the same directory as this script.")
        print("Current directory:", os.getcwd())
        return
    
    # Load data
    print("Loading data.txt...")
    corpus = load_corpus("data.txt")
    print(f"Loaded {len(corpus)} lines")
    
    if len(corpus) < 10:
        print("Warning: Corpus is very small. Training may not be effective.")
    
    # Split into train/val (90/10)
    random.seed(42)  # For reproducibility
    random.shuffle(corpus)
    
    split_idx = int(len(corpus) * 0.9)
    train_corpus = corpus[:split_idx]
    val_corpus = corpus[split_idx:]
    
    print(f"\nSplit:")
    print(f"  Training set: {len(train_corpus)} lines")
    print(f"  Validation set: {len(val_corpus)} lines")
    
    # Save splits (optional)
    os.makedirs("splits", exist_ok=True)
    with open("splits/train.txt", 'w', encoding='utf-8') as f:
        f.write("\n".join(train_corpus))
    with open("splits/val.txt", 'w', encoding='utf-8') as f:
        f.write("\n".join(val_corpus))
    print("Splits saved to 'splits/' directory")
    
    # Train with different merge values
    merge_values = [0, 2000, 8000]
    
    for num_merges in merge_values:
        print(f"\n{'='*60}")
        print(f"Training with num_merges = {num_merges}")
        print(f"{'='*60}")
        
        # Initialize and train tokenizer
        tokenizer = BPETokenizer()
        
        if num_merges == 0:
            print("Training without merges (character-level tokenizer)...")
        else:
            print(f"Training with {num_merges} BPE merges...")
        
        tokenizer.train(train_corpus, num_merges, verbose=True)
        
        # Test encode/decode on validation set
        print("\nTesting encode/decode on validation set...")
        test_samples = min(50, len(val_corpus))
        correct = 0
        
        for i in range(test_samples):
            text = val_corpus[i]
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            
            if decoded == text:
                correct += 1
            else:
                if i < 3:  # Show first 3 failures
                    print(f"  Sample {i}: FAIL")
                    print(f"    Original: '{text[:50]}...'" if len(text) > 50 else f"    Original: '{text}'")
                    print(f"    Decoded:  '{decoded[:50]}...'" if len(decoded) > 50 else f"    Decoded:  '{decoded}'")
        
        accuracy = correct / test_samples * 100
        print(f"Decode accuracy: {correct}/{test_samples} = {accuracy:.1f}%")
        
        # Calculate average sequence length
        total_tokens = 0
        total_texts = min(100, len(val_corpus))
        
        for i in range(total_texts):
            ids = tokenizer.encode(val_corpus[i])
            total_tokens += len(ids)
        
        avg_length = total_tokens / total_texts if total_texts > 0 else 0
        print(f"Average sequence length: {avg_length:.1f} tokens")
        
        # Save the model with 8000 merges
        if num_merges == 8000:
            tokenizer.save("bpe_tokenizer_8000.json")
            print(f"\nModel saved to 'bpe_tokenizer_8000.json'")
            print(f"Vocabulary size: {len(tokenizer.vocab)} tokens")
    
    # Also save merge rules separately
    if os.path.exists("bpe_tokenizer_8000.json"):
        print(f"\n{'='*60}")
        print("Creating bpe_merges.json with merge rules...")
        
        with open("bpe_tokenizer_8000.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open("bpe_merges.json", 'w', encoding='utf-8') as f:
            json.dump(data['merges'], f, ensure_ascii=False, indent=2)
        
        print("Merge rules saved to 'bpe_merges.json'")
    
    print(f"\n{'='*60}")
    print("Training completed successfully!")
    print("Created files:")
    print("  - bpe_tokenizer_8000.json (final trained model)")
    print("  - bpe_merges.json (merge rules)")
    print("  - splits/train.txt (training split)")
    print("  - splits/val.txt (validation split)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
