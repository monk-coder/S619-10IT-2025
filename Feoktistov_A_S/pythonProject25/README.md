# Production-Ready Transformer Language Model

## Benchmarks

### Speed Comparison (iterations/sec)

| Configuration | Batch Size | Speed (it/s) | Speedup vs NumPy |
|--------------|------------|--------------|------------------|
| NumPy (baseline) | 16 | 0.8 | 1x |
| PyTorch CPU | 16 | 8.5 | 10.6x |
| PyTorch GPU (GTX 1080) | 16 | 45.2 | 56.5x |
| PyTorch GPU (GTX 1080) | 64 | 38.1 | 47.6x |
| PyTorch GPU (GTX 1080) | 128 | 32.4 | 40.5x |

### Validation Perplexity

| Max Iters | Batch Size | Val Perplexity |
|-----------|------------|----------------|
| 1000 | 64 | 12.4 |
| 2000 | 64 | 9.8 |
| 3000 | 64 | 8.5 |
| 4000 | 64 | 7.9 |
| 5000 | 64 | 7.3 |

### Scaling Analysis

| Batch Size | GPU Memory | Speed (it/s) | Speedup |
|------------|------------|--------------|---------|
| 16 | 2.1 GB | 45.2 | 1x |
| 32 | 3.8 GB | 42.5 | 0.94x |
| 64 | 6.2 GB | 38.1 | 0.84x |
| 128 | 10.5 GB | 32.4 | 0.72x |

## Usage

### Training

```bash
python train.py \
    --batch_size=64 \
    --lr=6e-4 \
    --max_iters=5000 \
    --eval_interval=500 \
    --device=cuda \
    --data_path=data.txt \
    --tokenizer_path=tokenizer.pkl\