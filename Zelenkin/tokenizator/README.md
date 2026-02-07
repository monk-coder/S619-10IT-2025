# BPE Tokenizer - реализация с нуля

## Описание
Полная реализация Byte Pair Encoding (BPE) токенизатора с нуля...

## Установка
```bash
pip install -r requirements.txt

Использование
# Запуск эксперимента с разными num_merges
python bpe_tokenizer_full.py --mode experiment --num_merges 0 500 2000

# Интерактивное тестирование
python bpe_tokenizer_full.py --mode test

# Обучение и сохранение токенизатора
python bpe_tokenizer_full.py --mode train --num_merges 1000 --save_model my_model.json

Примеры
from bpe_tokenizer_full import BPETokenizer

tokenizer = BPETokenizer()
tokenizer.train(corpus, num_merges=1000)
encoded = tokenizer.encode("Привет мир!")
decoded = tokenizer.decode(encoded)
print(decoded)  # "Привет мир!"

