# Transformer Language Model (NumPy Implementation)

Decoder-only Transformer language model trained from scratch using only NumPy.

## Architecture

- **Tokenizer**: BPE (Byte Pair Encoding) with ~5000 merges
- **Model**: 3-layer decoder-only Transformer
  - 4 attention heads
  - Embedding dimension: 192
  - Feed-forward dimension: 768
  - Context window: 128 tokens
- **Training**: Adam optimizer with learning rate warmup
- **Loss**: Cross-entropy for next-token prediction

## Installation

```bash
python -m venv venv
source venv/bin/activate   # Linux/MacOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt