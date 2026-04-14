# Результаты эксперимента на SQuAD 2.0

## Метрики (на validation)

| Method              | Exact Match (%) | F1 Score (%) |
|---------------------|-----------------|---------------|
| Zero-shot           | 19.2            | 28.4          |
| Few-shot (5 shots)  | 24.7            | 34.1          |
| LoRA (r=16)         | 53.8            | 61.3          |

## Улучшение
- LoRA лучше zero-shot на **32.9%** по F1
- LoRA лучше few-shot на **27.2%** по F1

## Условия эксперимента
- Модель: Llama-3.2-1B
- Quantization: 4-bit NF4
- LoRA rank: 16
- Training steps: 500
- Batch size: 4
- Learning rate: 2e-4