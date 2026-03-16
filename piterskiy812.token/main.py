#!/usr/bin/env python3
"""
BPE Tokenizer Test
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bpe_tokenizer import BPETokenizer

def main():
    print("Testing BPE Tokenizer...")
    
    # Create test data
    corpus = [
        "hello world",
        "machine learning",
        "neural networks",
        "python programming",
        "test sentence"
    ]
    
    # Train tokenizer
    tokenizer = BPETokenizer()
    tokenizer.train(corpus, num_merges=10, verbose=False)
    
    # Test encode/decode
    test_text = "hello world"
    encoded = tokenizer.encode(test_text)
    decoded = tokenizer.decode(encoded)
    
    print(f"Input: '{test_text}'")
    print(f"Encoded: {encoded}")
    print(f"Decoded: '{decoded}'")
    
    # Check if decode(encode(text)) == text
    if decoded == test_text:
        print("✅ Test PASSED")
        sys.exit(0)
    else:
        print("❌ Test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
