#!/usr/bin/env python3
"""
Entry point for BPE Tokenizer assignment.
GitHub Classroom will run this file to test your implementation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bpe_tokenizer import BPETokenizer
    
    def test_bpe_tokenizer():
        """Test BPE Tokenizer basic functionality."""
        print("Testing BPE Tokenizer Implementation")
        print("=" * 60)
        
        # Create a test corpus if data.txt doesn't exist
        if not os.path.exists("data.txt"):
            print("Creating test data.txt...")
            test_data = [
                "the quick brown fox jumps over the lazy dog",
                "hello world this is a test sentence",
                "machine learning and artificial intelligence",
                "natural language processing with python",
                "deep learning neural networks transformers",
                "bpe tokenization algorithm implementation",
                "subword segmentation for text processing",
                "computer science and programming languages"
            ]
            with open("data.txt", "w", encoding="utf-8") as f:
                for line in test_data:
                    f.write(line + "\n")
            print(f"Created data.txt with {len(test_data)} lines")
        
        # Load data
        print("\nLoading training data...")
        with open("data.txt", "r", encoding="utf-8") as f:
            corpus = [line.strip() for line in f if line.strip()]
        
        if len(corpus) < 3:
            print("❌ ERROR: Not enough data in data.txt")
            return False
        
        print(f"Loaded {len(corpus)} lines from data.txt")
        print(f"Sample: '{corpus[0][:50]}...'" if len(corpus[0]) > 50 else f"Sample: '{corpus[0]}'")
        
        # Split into train/test
        train_size = max(5, len(corpus) // 2)
        train_corpus = corpus[:train_size]
        test_corpus = corpus[train_size:min(train_size + 3, len(corpus))]
        
        print(f"\nTraining on {len(train_corpus)} lines...")
        
        # Initialize and train tokenizer
        tokenizer = BPETokenizer()
        
        # Train with a small number of merges for quick testing
        num_merges = min(50, len(train_corpus) * 2)
        print(f"Performing {num_merges} BPE merge operations...")
        
        tokenizer.train(train_corpus, num_merges, verbose=False)
        
        print(f"\n✅ Training completed successfully!")
        print(f"   Vocabulary size: {len(tokenizer.vocab)} tokens")
        print(f"   BPE merges performed: {len(tokenizer.merges)}")
        
        # Test encode/decode
        print(f"\nTesting encode/decode on {len(test_corpus)} samples:")
        all_passed = True
        
        for i, text in enumerate(test_corpus):
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            
            if decoded == text:
                print(f"  Sample {i+1}: ✓ PASSED")
                print(f"    Tokens: {len(encoded)}")
            else:
                print(f"  Sample {i+1}: ✗ FAILED")
                print(f"    Original: '{text}'")
                print(f"    Decoded:  '{decoded}'")
                all_passed = False
        
        # Additional test: verify vocab is not empty
        if len(tokenizer.vocab) < 10:
            print(f"\n⚠️  WARNING: Vocabulary is very small ({len(tokenizer.vocab)} tokens)")
            print("   This might indicate a problem with training")
        
        # Test save/load functionality
        print(f"\nTesting save/load functionality...")
        try:
            tokenizer.save("test_model.json")
            
            new_tokenizer = BPETokenizer()
            new_tokenizer.load("test_model.json")
            
            # Test that loaded tokenizer works
            test_text = "hello world"
            encoded1 = tokenizer.encode(test_text)
            encoded2 = new_tokenizer.encode(test_text)
            
            if encoded1 == encoded2:
                print("  ✓ Save/load test PASSED")
            else:
                print("  ✗ Save/load test FAILED")
                all_passed = False
            
            # Clean up test file
            if os.path.exists("test_model.json"):
                os.remove("test_model.json")
                
        except Exception as e:
            print(f"  ✗ Save/load test FAILED: {e}")
            all_passed = False
        
        print(f"\n{'='*60}")
        if all_passed:
            print("✅ ALL TESTS PASSED!")
            print("✅ BPE Tokenizer implementation is working correctly")
            print(f"✅ Trained on {len(train_corpus)} lines from data.txt")
            print(f"✅ Vocabulary size: {len(tokenizer.vocab)} tokens")
            print(f"✅ encode() and decode() functions work properly")
            print(f"{'='*60}")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            print("   Please check your implementation")
            print(f"{'='*60}")
            return False
    
    if __name__ == "__main__":
        success = test_bpe_tokenizer()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
