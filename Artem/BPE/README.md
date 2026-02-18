# BPE Tokenizer Implementation

Byte Pair Encoding (BPE) tokenizer implemented from scratch in pure Python + NumPy.
Based on Sennrich et al. "Neural Machine Translation of Rare Words with Subword Units".

## Features

- ✅ Full BPE training pipeline (character initialization → iterative merges)
- ✅ Lossless reconstruction: `decode(encode(text)) == text`
- ✅ Preserves whitespace and Unicode characters
- ✅ Optimized O(n) merge application (no quadratic bottlenecks)
- ✅ Train/val split with reproducibility
- ✅ Metrics: vocab size, avg token length, long-sequence analysis
- ✅ Experiment framework for comparing `num_merges` values
- ✅ Save/load tokenizer state (merges + vocab)

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt