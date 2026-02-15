# BPE Tokenizer Implementation

Byte Pair Encoding (BPE) tokenizer implementation from scratch, following Sennrich et al.'s approach for subword segmentation.

## Features

- Pure Python implementation (no PyTorch/TensorFlow)
- Efficient O(n) pair counting with frequency-aware merging
- Exact reconstruction guarantee: `decode(encode(text)) == text`
- Word boundary preservation with `</w>` markers
- Special tokens support (`<PAD>`, `<UNK>`, `<BOS>`, `<EOS>`)
- Deterministic behavior with sorted vocabulary
- Comprehensive metrics and visualization

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/MacOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic API

```python
from bpe_tokenizer import BPETokenizer

# Initialize tokenizer
tokenizer = BPETokenizer()

# Train on corpus (list of text documents)
corpus = ["This is a sample text.", "Another example sentence."]
tokenizer.train(corpus, num_meres=1000)

# Encode text to token IDs
text = "Hello world!"
ids = tokenizer.encode(text, add_special_tokens=True)
print(ids)  # [2, 154, 87, 3]  (<BOS>, "Hello", "world!", <EOS>)

# Decode back to text
reconstructed = tokenizer.decode(ids, skip_special_tokens=True)
print(reconstructed)  # "Hello world!"

# Save tokenizer
tokenizer.save("my_tokenizer.json")

# Load tokenizer later
tokenizer2 = BPETokenizer()
tokenizer2.load("my_tokenizer.json")
```

### Training on Your Corpus

1. Place your corpus file as `data.txt` in the BPE folder (UTF-8 encoded)
2. Run the training script:

```bash
python train.py
```

This will:
- Split corpus into train/validation sets (90/10)
- Train tokenizers with different `num_merges` values (0, 2k, 8k)
- Evaluate reconstruction accuracy and sequence lengths
- Generate metrics visualization (`bpe_metrics.png`)
- Save tokenizers as `bpe_merges_{N}.json`

## Project Structure

```
BPE/
├── bpe_tokenizer.py       # Core tokenizer implementation
├── train.py               # Training script and experiments
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── data.txt               # Your corpus file (input)
├── bpe_merges_*.json      # Saved tokenizer states (output)
├── bpe_metrics.png        # Metrics visualization (output)
└── experiment_results.json # Experiment results (output)
```

## Key Design Decisions

1. **Word Segmentation**: Uses regex pattern for robust word boundary detection
2. **Efficiency**: 
   - Counts pairs across entire corpus in O(n) per iteration
   - Uses word frequency aggregation to avoid processing duplicates
3. **Reconstruction Guarantee**: 
   - Preserves word boundaries with `</w>` markers
   - Careful whitespace handling during decode
4. **Vocabulary Building**: 
   - Starts with all unique characters
   - Adds merged tokens incrementally
   - Sorts tokens by length then lexicographically for deterministic IDs

## Validation

The implementation guarantees exact reconstruction on validation set:

```python
assert tokenizer.decode(tokenizer.encode(text)) == text
```

## References

- Sennrich, R., Haddow, B., & Birch, A. (2016). "Neural Machine Translation of Rare Words with Subword Units". ACL.