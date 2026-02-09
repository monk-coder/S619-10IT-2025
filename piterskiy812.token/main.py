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
    
    def test_basic_functionality():
        """Test that tokenizer can be trained on real data."""
        print("Testing BPE Tokenizer...")
        
        # Check if we can load and train on data.txt
        if not os.path.exists("data.txt"):
            print("❌ ERROR: data.txt not found!")
            print("Please make sure data.txt is in the same directory")
            return False
        
        print("✅ data.txt found")
        
        # Try to read the file
        try:
            with open("data.txt", 'r', encoding='utf-8') as f:
                # Just read first few lines to check
                lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # Read only first 10 lines for quick test
                        break
                    stripped = line.strip()
                    if stripped:
                        lines.append(stripped)
                
                if len(lines) < 3:
                    print("❌ ERROR: data.txt seems empty or has too few lines")
                    return False
                
                print(f"✅ Successfully read {len(lines)} lines from data.txt")
                print(f"   First line: '{lines[0][:50]}...'" if len(lines[0]) > 50 else f"   First line: '{lines[0]}'")
                
                # Use these lines for training
                train_corpus = lines
                
        except Exception as e:
            print(f"❌ ERROR reading data.txt: {e}")
            return False
        
        # Initialize and train tokenizer
        print("\nTraining BPE tokenizer...")
        tokenizer = BPETokenizer()
        
        # Train on the small sample
        num_merges = 20  # Small number for quick test
        tokenizer.train(train_corpus, num_merges, verbose=True)
        
        print(f"\n✅ Training completed!")
        print(f"   Vocabulary size: {len(tokenizer.vocab)} tokens")
        print(f"   BPE merges performed: {len(tokenizer.merges)}")
        
        # Test encode/decode
        print("\nTesting encode/decode...")
        all_passed = True
        
        for i, text in enumerate(train_corpus[:3]):
            encoded = tokenizer.encode(text)
            decoded = tokenizer.decode(encoded)
            
            if decoded == text:
                print(f"  Sample {i+1}: ✓ PASSED")
            else:
                print(f"  Sample {i+1}: ✗ FAILED")
                print(f"    Original: '{text}'")
                print(f"    Decoded:  '{decoded}'")
                all_passed = False
        
        if all_passed:
            print(f"\n{'='*60}")
            print("✅ ALL TESTS PASSED!")
            print(f"✅ Tokenizer successfully trained on data from data.txt")
            print(f"✅ Vocabulary size: {len(tokenizer.vocab)} tokens")
            print(f"✅ BPE merges: {len(tokenizer.merges)}")
            print(f"✅ encode/decode works correctly")
            print(f"{'='*60}")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
    
    if __name__ == "__main__":
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
