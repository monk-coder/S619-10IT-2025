#!/usr/bin/env python3
"""
Entry point for the BPE tokenizer assignment.
This file is required by GitHub Classroom.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bpe_tokenizer import BPETokenizer
    
    def test_basic_functionality():
        """Test basic encode/decode functionality."""
        print("Testing BPE Tokenizer basic functionality...")
        
        # Create a simple corpus
        corpus = [
            "hello world",
            "hello there",
            "good morning",
            "how are you",
            "test sentence for bpe"
        ]
        
        # Initialize and train tokenizer
        tokenizer = BPETokenizer()
        tokenizer.train(corpus, num_merges=10, verbose=False)
        
        # Test encode/decode
        test_text = "hello"
        encoded = tokenizer.encode(test_text)
        decoded = tokenizer.decode(encoded)
        
        print(f"Test text: '{test_text}'")
        print(f"Encoded: {encoded}")
        print(f"Decoded: '{decoded}'")
        
        # Verify
        if decoded == test_text:
            print("✓ Basic functionality test PASSED")
            return True
        else:
            print("✗ Basic functionality test FAILED")
            return False
    
    if __name__ == "__main__":
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
