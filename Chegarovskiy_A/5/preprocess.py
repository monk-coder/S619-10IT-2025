import json
import numpy as np


def encode_text(text, vocab, merges, word_end):
    tokens = []
    words = text.split()
    for word in words:
        chars = list(word) + [word_end]
        tokens.extend(chars)
    for a, b in merges:
        new_token = a + b
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == a and tokens[i+1] == b:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return [vocab.get(t, 0) for t in tokens]


# Загрузка BPE
with open('bpe_8000.json', 'r', encoding='utf-8') as f:
    bpe_data = json.load(f)

vocab = bpe_data['vocab']
merges = [tuple(m) for m in bpe_data['merges']]
word_end = bpe_data['word_end']

# Загрузка текста
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Токенизация (один раз, долго)
print("Токенизация...")
tokens = encode_text(text, vocab, merges, word_end)

# Сохранение
np.save('tokens.npy', np.array(tokens, dtype=np.int32))
print(f"Сохранено {len(tokens)} токенов в tokens.npy")