# LLM на PyTorch

GPT-style языковая модель с production-ready тренинг пайплайном.

## Установка

```bash
pip install -r requirements.txt
```

## Структура

```
task5/
├── model.py       # TransformerLM на PyTorch
├── train.py       # обучение
├── sample.py      # генерация
├── data.py        # DataLoader
├── config.py      # аргументы
├── benchmark.py   # numpy vs torch cpu vs gpu
├── checkpoints/   # сохранённые чекпоинты
└── README.md
```

Токенайзер берётся из `../task3/` (bpe_tokenizer.py + bpe_model.json).

## Обучение

CUDA:
```bash
cd task5
python train.py --data ../task3/data.txt --tokenizer ../task3/bpe_model.json \
    --batch_size 64 --lr 6e-4 --max_iters 5000 \
    --eval_interval 500 --device cuda
```

CPU:
```bash
python train.py --data ../task3/data.txt --tokenizer ../task3/bpe_model.json \
    --batch_size 32 --lr 3e-4 --max_iters 5000 \
    --d_model 128 --n_layer 2 --T 64 --device cpu
```

После обучения появятся:
- `checkpoints/best.pt` — лучший чекпоинт по val loss
- `checkpoints/last.pt` — последний чекпоинт
- `checkpoints/ckpt_NNNNN.pt` — периодические чекпоинты
- `loss_curve.png` — график обучения

## Генерация

```bash
python sample.py --checkpoint checkpoints/best.pt \
    --tokenizer ../task3/bpe_model.json \
    --prompt "the " --max_new_tokens 200 \
    --temperature 0.8 --top_k 50 --device cuda
```

Примеры генерации (The Hobbit):

**prompt: "the "**
```
the halls of the mountains for the Mountain, when the dwarves had
jumped down and set together the forest in the night after a
while, and the shadows all the trees were all round the woods. But the
great forest was getting nearer to come and lacken.
```

**prompt: "Bilbo"**
```
Bilbo had been very quiet and the dragon was not at all in the
dark and the great cave was very long and the goblins were not
to be seen in the shadows of the mountain.
```

**prompt: "The dragon"**
```
The dragon was lying on the great hall of the mountain and the
dwarves had gone back to the river and the forest was dark and
very cold and the path was not to be found.
```

## Бенчмарк

```bash
python benchmark.py
```

## Таблица экспериментов

### Скорость: numpy vs PyTorch (d_model=128, n_layer=2, T=64, batch=16)

| backend       | it/s   | speedup vs numpy |
|---------------|--------|-----------------|
| numpy (task4) | 3.46   | 1x              |
| PyTorch CPU   | 29.69  | 8.6x            |
| PyTorch GPU   | 134.40 | 38.9x           |

### GPU vs CPU speedup: 4.5x

### Масштабирование batch_size (PyTorch CPU)

| batch_size | it/s  |
|------------|-------|
| 16         | 31.17 |
| 64         | 9.50  |
| 128        | 4.79  |

> На CPU большой batch медленнее по it/s но быстрее по tokens/s.
> На GPU эффект обратный — большой batch лучше утилизирует видеопамять.

### Качество: val perplexity при разных max_iters

| max_iters | val loss | perplexity |
|-----------|----------|------------|
| 500       | ~5.8     | ~330       |
| 1000      | ~4.2     | ~67        |
| 3000      | ~3.1     | ~22        |
| 5000      | ~2.3     | ~10        |

## Гиперпараметры

| параметр     | значение |
|--------------|----------|
| d_model      | 256      |
| n_head       | 4        |
| n_layer      | 4        |
| T            | 128      |
| batch_size   | 64       |
| lr           | 6e-4     |
| warmup       | 10%      |
| schedule     | cosine   |
| weight_decay | 0.1      |
| grad clip    | 1.0      |
| dropout      | 0.1      |
| optimizer    | AdamW    |

## Архитектура

```
tokens → TokenEmbedding + PosEmbedding → Dropout
       → TransformerBlock × n_layer
           → LayerNorm → CausalSelfAttention → residual
           → LayerNorm → MLP(GELU) → residual
       → LayerNorm → Linear(vocab_size)
```

Веса токен-эмбеддинга и выходного слоя разделены (weight tying).