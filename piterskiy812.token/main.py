#!/usr/bin/env python3
"""
Entry point for the BPE tokenizer assignment.
This file is required by GitHub Classroom.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bpe_tokenizer import BPETokenizer
    
    def test_real_training():
        """Test that tokenizer can be trained on data.txt."""
        print("Testing BPE Tokenizer with data.txt...")
        
        # Check if data.txt exists
        if not os.path.exists("data.txt"):
            print("❌ ERROR: data.txt not found!")
            print("Current directory:", os.getcwd())
            return False
        
        # Load data.txt and check size
        print("Loading data.txt...")
        try:
            with open("data.txt", 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    stripped = line.strip()
                    if stripped:  # Skip empty lines
                        lines.append(stripped)
        except Exception as e:
            print(f"❌ ERROR reading data.txt: {e}")
            return False
        
        print(f"Loaded {len(lines)} lines from data.txt")
        
        if len(lines) < 10:
            print("❌ ERROR: data.txt has too few lines!")
            print("Expected at least 10 lines, got", len(lines))
            return False
        
        # Use reasonable sample for testing (not all 36k)
        sample_size = min(500, len(lines))
        corpus = lines[:sample_size]
        print(f"Using {sample_size} lines for testing (out of {len(lines)})")
        
        # Initialize and train tokenizer
        tokenizer = BPETokenizer()
        
        # Train with reasonable number of merges
        num_merges = 100  # Small for testing
        print(f"Training with {num_merges} merges...")
        
        tokenizer.train(corpus, num_merges, verbose=True)
        
        print(f"\nTraining completed.")
        print(f"Vocabulary size: {len(tokenizer.vocab)} tokens")
        print(f"Number of merges learned: {len(tokenizer.merges)}")
        
        # Test encode/decode on multiple samples
        test_samples = min(5, len(corpus))
        all_passed = True
        
        print(f"\nTesting encode/decode on {test_samples} samples:")
        for i in range(test_samples):
            text = corpus[i]
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            
            # Show first sample in detail
            if i == 0:
                print(f"\nSample 1 details:")
                print(f"  Original text: '{text}'")
                print(f"  Encoded IDs: {encoded}")
                print(f"  Number of tokens: {len(encoded)}")
                print(f"  Decoded text: '{decoded}'")
            
            if decoded == text:
                print(f"  Sample {i+1}: ✓ PASSED")
            else:
                print(f"  Sample {i+1}: ✗ FAILED")
                all_passed = False
        
        # Additional test: check that encode/decode preserves exact text
        print(f"\n{'='*60}")
        if all_passed:
            print("✅ SUCCESS: All encode/decode tests passed!")
            print(f"✅ Tokenizer correctly trained on {sample_size} lines from data.txt")
            print(f"✅ Vocabulary size: {len(tokenizer.vocab)}")
            print(f"✅ BPE merges: {len(tokenizer.merges)}")
            return True
        else:
            print("❌ FAILURE: Some encode/decode tests failed")
            return False
    
    if __name__ == "__main__":
        success = test_real_training()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
