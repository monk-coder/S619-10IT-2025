# LLM Training Pipeline

Production-ready GPT model implementation with PyTorch.

## Features

- Professional training pipeline with configurable parameters
- AdamW optimizer with cosine annealing schedule
- Gradient clipping for stable training
- Mixed precision training (FP16)
- Automatic checkpointing with best model saving
- Evaluation with perplexity metric
- Text generation with temperature and top-k sampling

## Installation

```bash
pip install -r requirements.txt
```
## Use for learn
```bash
python train.py --batch_size=64 --lr=6e-4 --max_iters=5000 --eval_interval=500 --device=cuda
```
## Use for generate
```bash
# Более детерминированная генерация (низкая температура)
python sample.py --checkpoint=checkpoints/best_model.pt --prompt="ROMEO:" --temperature=0.5 --top_k=20

# Более креативная генерация (высокая температура)
python sample.py --checkpoint=checkpoints/best_model.pt --prompt="ROMEO:" --temperature=1.2 --top_k=100
```