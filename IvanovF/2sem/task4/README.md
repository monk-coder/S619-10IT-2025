# GPT с нуля на numpy — Task 4

Языковая модель в стиле GPT, написанная полностью на numpy без PyTorch и других autograd-фреймворков. Модель учится предсказывать следующий токен и генерирует текст.

## Установка

```bash
pip install -r requirements.txt
```

## Структура файлов

```
task4/
├── model.py      # TransformerLM, все слои, backward вручную
├── dataset.py    # построение датасета из BPE токенов
├── train.py      # обучение
├── sample.py     # генерация текста
├── requirements.txt
└── README.md

task3/            # токенайзер берётся отсюда
├── bpe_tokenizer.py
├── bpe_model.json
└── data.txt
```

## Обучение

```bash
cd task4
python train.py --data ../task3/data.txt --tokenizer ../task3/bpe_model.json
```

Все параметры:

```bash
python train.py \
  --data ../task3/data.txt \
  --tokenizer ../task3/bpe_model.json \
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

Если `bpe_model.json` не существует — токенайзер обучится автоматически.

После обучения появятся:
- `gpt_model.npz` — веса модели
- `gpt_model_config.json` — конфиг архитектуры
- `loss_curve.png` — график обучения

## Генерация

```bash
python sample.py \
  --model gpt_model \
  --tokenizer ../task3/bpe_model.json \
  --prompt "the quick" \
  --max_new_tokens 100 \
  --temperature 0.8 \
  --top_k 20
```

| параметр | что делает |
|---|---|
| `--prompt` | начало текста |
| `--max_new_tokens` | сколько токенов сгенерировать |
| `--temperature` | 0.5 = предсказуемо, 1.0 = разнообразно |
| `--top_k` | выбирать только из топ-k токенов |

## Как это работает

### 1. Токенизация

Текст переводится в числа через BPE токенайзер из task3:

```
"hello world" → [45, 12, 300]
```

BPE склеивает частые буквосочетания в один токен — так словарь получается компактным.

### 2. Датасет

Из токенов строятся пары вход → цель со сдвигом на 1:

```
текст:  [1, 2, 3, 4, 5]
вход x: [1, 2, 3, 4]
цель y: [2, 3, 4, 5]
```

Модель учится: видя `[1, 2, 3, 4]` — предсказать `5`.

### 3. Архитектура

```
токены → TokenEmbedding + PosEmbedding
       → TransformerBlock x n_layer
           → LayerNorm
           → CausalSelfAttention
           → residual (+x)
           → LayerNorm
           → MLP (GELU)
           → residual (+x)
       → LayerNorm
       → Linear → logits (vocab_size)
```

**Embedding** — каждый токен превращается в вектор из 128 чисел. Плюс добавляется позиционный вектор — чтобы модель знала где стоит токен.

**CausalSelfAttention** — каждый токен смотрит на все предыдущие и решает на что обратить внимание. Будущее закрыто маской:

```
позиция:  1  2  3  4
1:        V  X  X  X
2:        V  V  X  X
3:        V  V  V  X
4:        V  V  V  V
```

**MLP** — два линейных слоя с GELU между ними. Обрабатывает каждый токен независимо.

**Residual connection** — результат каждого блока прибавляется к входу. Защищает от потери информации в глубоких сетях.

### 4. Обучение

На каждом шаге:
1. Прямой проход — получаем logits
2. Считаем cross-entropy loss
3. Обратный проход — считаем градиенты вручную
4. Adam обновляет веса

Весь backward написан вручную без autograd — для каждого слоя отдельно.

### 5. Генерация

```
prompt → encode → [45, 12]
                      |
              forward через модель
                      |
          logits последней позиции
                      |
            делим на temperature
                      |
              softmax → вероятности
                      |
       выбираем случайно из top-k
                      |
            добавляем к контексту
                      |
               повторяем N раз
```

## Гиперпараметры

| параметр | значение | что это |
|---|---|---|
| d_model | 128 | размер векторов |
| n_head | 4 | голов внимания |
| n_layer | 2 | блоков трансформера |
| T | 64 | длина контекста в токенах |
| batch_size | 32 | примеров за шаг |
| lr | 3e-4 | скорость обучения |
| optimizer | Adam | алгоритм оптимизации |

## Время обучения

| конфиг | время одной эпохи (100 шагов) |
|---|---|
| d_model=128, n_layer=2, CPU | ~55 сек |
