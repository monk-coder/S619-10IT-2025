# Transformer Language Model from scratch (numpy only)

Реализация decoder-only Transformer (как в GPT) на чистом numpy с обратным распространением.

## Гиперпараметры

- vocab_size = 1000 (BPE токенизатор)
- d_model = 128
- n_head = 4
- n_layer = 3
- max_seq_len = 128
- batch_size = 32
- learning_rate = 0.001 (Adam)
- epochs = 10

## Обучение

```bash
python train.py
