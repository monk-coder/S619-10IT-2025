# Production LLM Training Pipeline (PyTorch)

Decoder-only Transformer с AdamW, cosine warmup, mixed precision, gradient clipping и checkpointing.

## 🚀 Быстрый старт
```bash
pip install -r requirements.txt
python train.py --batch_size=64 --lr=6e-4 --max_iters=5000 --eval_interval=500 --device=cuda
python sample.py --checkpoint=checkpoints/ckpt_best.pt --prompt "ROMEO:" --max_new_tokens=200 --temperature=0.8 --top_k=50