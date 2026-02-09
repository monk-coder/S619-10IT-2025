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
            print("Please download data.txt to this directory")
            return False
        
        # Load a small sample from data.txt
        print("Loading sample from data.txt...")
        with open("data.txt", 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if len(lines) < 10:
            print("❌ ERROR: data.txt has too few lines")
            return False
        
        sample_size = min(100, len(lines))
        corpus = lines[:sample_size]
        print(f"Using {sample_size} lines from data.txt for testing")
        
        # Initialize and train tokenizer
        tokenizer = BPETokenizer()
        
        # Train with reasonable number of merges
        num_merges = min(500, sample_size * 2)  # Adaptive based on corpus size
        print(f"Training with {num_merges} merges...")
        
        tokenizer.train(corpus, num_merges, verbose=False)
        
        print(f"Training completed. Vocabulary size: {len(tokenizer.vocab)}")
        
        # Test encode/decode on multiple samples
        test_samples = min(10, len(corpus))
        all_passed = True
        
        print(f"\nTesting encode/decode on {test_samples} samples...")
        for i in range(test_samples):
            text = corpus[i]
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            
            if decoded == text:
                print(f"  Sample {i+1}: ✓ PASSED")
            else:
                print(f"  Sample {i+1}: ✗ FAILED")
                print(f"    Original: '{text[:50]}...'" if len(text) > 50 else f"    Original: '{text}'")
                print(f"    Decoded:  '{decoded[:50]}...'" if len(decoded) > 50 else f"    Decoded:  '{decoded}'")
                all_passed = False
        
        # Test metrics function
        try:
            from bpe_tokenizer import calculate_metrics
            metrics = calculate_metrics(tokenizer, corpus[:20])
            print(f"\nMetrics on 20 samples:")
            print(f"  Average sequence length: {metrics['avg_length']:.1f} tokens")
            print(f"  Vocabulary size: {metrics['vocab_size']}")
        except:
            pass
        
        if all_passed:
            print("\n✅ All tests PASSED - BPE Tokenizer works correctly!")
            return True
        else:
            print("\n❌ Some tests FAILED")
            return False
    
    if __name__ == "__main__":
        success = test_real_training()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
