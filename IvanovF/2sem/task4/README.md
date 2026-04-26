# GPT от нуля на numpy

Decoder-only Transformer (GPT-style) обученный предсказывать следующий токен. Всё реализовано вручную на numpy: forward, backward, Adam.

## Установка

```bash
pip install -r requirements.txt
```

## Структура файлов

```
task4/
├── model.py          # TransformerLM, LayerNorm, Attention, MLP, Adam
├── dataset.py        # построение датасета из BPE токенов
├── train.py          # обучение
├── sample.py         # генерация текста
├── bpe_tokenizer.py  # BPE из task3
├── utils.py          # load_data, split_corpus
├── requirements.txt
└── README.md
```

## Обучение

Сначала нужен файл `data.txt` в папке (или укажите путь через `--data`).

```bash
python train.py \
  --data data.txt \
  --tokenizer bpe_model.json \
  --n_merges 2000 \
  --d_model 128 \
  --n_head 4 \
  --n_layer 2 \
  --T 64 \
  --batch_size 32 \
  --lr 3e-4 \
  --epochs 20 \
  --steps_per_epoch 200 \
  --save gpt_model \
  --plot loss_curve.png
```

Если `bpe_model.json` не существует, токенайзер обучится автоматически.

После обучения появятся:
- `gpt_model.npz` — веса модели
- `gpt_model_config.json` — конфиг архитектуры
- `loss_curve.png` — график обучения

## Генерация

```bash
python sample.py \
  --model gpt_model \
  --tokenizer bpe_model.json \
  --prompt "the quick brown" \
  --max_new_tokens 50 \
  --temperature 0.8 \
  --top_k 20
```

Параметры:
- `--prompt` — начало текста
- `--max_new_tokens` — сколько токенов сгенерировать
- `--temperature` — чем ниже, тем детерминированнее (0.5–1.0 хорошо)
- `--top_k` — сэмплировать только из топ-k токенов

## Гиперпараметры и время обучения

| параметр | значение |
|---|---|
| d_model | 128 |
| n_head | 4 |
| n_layer | 2 |
| T (context) | 64 |
| batch_size | 32 |
| lr | 3e-4 |
| optimizer | Adam (β1=0.9, β2=0.999) |
| weight_decay | 0.01 |

Время одной эпохи (100 шагов, CPU): ~55 секунд.

## Архитектура

```
tokens → TokenEmbedding + PosEmbedding
       → TransformerBlock × n_layer
           → LayerNorm → CausalSelfAttention → residual
           → LayerNorm → MLP(GELU) → residual
       → LayerNorm → Linear → logits (vocab_size)
```

Backward реализован вручную для каждого слоя.