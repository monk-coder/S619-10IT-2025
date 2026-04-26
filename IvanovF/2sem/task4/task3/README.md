# BPE Tokenizer

Субсловный токенайзер на основе Byte Pair Encoding, написанный с нуля на Python.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

### Обучение

```bash
python train.py --data 0/data.txt --merges 2000 --save_path bpe_model.json
```

Параметры:
- `--data` — путь к файлу с корпусом (обязательно)
- `--merges` — количество слияний (по умолчанию 2000)
- `--save_path` — куда сохранить модель (по умолчанию `bpe_model.json`)

### Оценка

```bash
python evaluate.py --model bpe_model.json --data 0/data.txt
```

### Сравнение разных num_merges (0 / 2000 / 8000)

```bash
python evaluate.py --data 0/data.txt --compare
```

## Примеры encode/decode

```python
from bpe_tokenizer import BPETokenizer

# загружаем обученную модель
tokenizer = BPETokenizer.load("bpe_model.json")

text = "Привет, мир!"
ids = tokenizer.encode(text)
print(ids)           # например [45, 12, 300, ...]

decoded = tokenizer.decode(ids)
print(decoded)       # "Привет, мир!"

# проверка что всё правильно
assert decoded == text  # всегда True
```

## Как это работает

**BPE (Byte Pair Encoding):**

1. Начинаем с алфавита из отдельных символов
2. Считаем все пары соседних токенов в корпусе
3. Самую частую пару заменяем новым токеном
4. Повторяем `num_merges` раз

**Оптимизация:** вместо того чтобы каждый раз пересчитывать все пары заново, мы обновляем только те пары, которые затронуло последнее слияние. Это ускоряет обучение примерно в 10-50 раз по сравнению с наивной реализацией.

**encode:** применяем merges в порядке их изучения (по рангу), всегда выбирая пару с наименьшим рангом.

**decode:** просто конкатенируем строки токенов.

## Структура файлов

```
BPE/
├── bpe_tokenizer.py   # основной класс BPETokenizer
├── train.py           # скрипт обучения
├── evaluate.py        # скрипт оценки и сравнения
├── utils.py           # load_data, split_corpus
├── requirements.txt
└── README.md
```