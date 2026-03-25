# create_bpe_tokenizer.py
import pickle
import os
from collections import defaultdict


class SimpleBPETokenizer:
    def __init__(self):
        self.vocab_size = 0
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.merges = {}  # пары для BPE

    def train(self, text, vocab_size=1000):
        """Обучает BPE токенизатор"""

        # Шаг 1: Начальный словарь из символов
        chars = sorted(list(set(text)))
        self.char_to_idx = {ch: i for i, ch in enumerate(chars)}
        self.idx_to_char = {i: ch for i, ch in enumerate(chars)}

        # Шаг 2: Разбиваем текст на слова
        words = text.split()
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1

        # Шаг 3: Преобразуем слова в списки символов
        word_splits = {word: list(word) for word in word_counts}

        # Шаг 4: Повторяем BPE слияния до достижения vocab_size
        current_vocab_size = len(chars)
        self.merges = {}

        while current_vocab_size < vocab_size:
            # Считаем частоты пар
            pair_counts = defaultdict(int)
            for word, count in word_counts.items():
                splits = word_splits[word]
                for i in range(len(splits) - 1):
                    pair = (splits[i], splits[i + 1])
                    pair_counts[pair] += count

            if not pair_counts:
                break

            # Находим самую частую пару
            best_pair = max(pair_counts, key=pair_counts.get)

            # Добавляем новый токен
            new_token = ''.join(best_pair)
            new_idx = current_vocab_size

            self.idx_to_char[new_idx] = new_token
            self.char_to_idx[new_token] = new_idx
            self.merges[best_pair] = new_idx

            # Обновляем разбиения слов
            for word in word_counts:
                splits = word_splits[word]
                new_splits = []
                i = 0
                while i < len(splits):
                    if i < len(splits) - 1 and (splits[i], splits[i + 1]) == best_pair:
                        new_splits.append(new_token)
                        i += 2
                    else:
                        new_splits.append(splits[i])
                        i += 1
                word_splits[word] = new_splits

            current_vocab_size += 1

        self.vocab_size = current_vocab_size
        print(f"Обучен BPE токенизатор")
        print(f"Размер словаря: {self.vocab_size}")
        print(f"Количество слияний: {len(self.merges)}")

    def encode(self, text):
        """Кодирует текст в индексы"""
        # Разбиваем на слова
        words = text.split()
        tokens = []

        for word in words:
            # Начинаем с отдельных символов
            splits = list(word)

            # Применяем все слияния
            for pair, new_token_idx in self.merges.items():
                new_splits = []
                i = 0
                while i < len(splits):
                    if i < len(splits) - 1 and (splits[i], splits[i + 1]) == pair:
                        new_splits.append(self.idx_to_char[new_token_idx])
                        i += 2
                    else:
                        new_splits.append(splits[i])
                        i += 1
                splits = new_splits

            # Преобразуем в индексы
            for token in splits:
                tokens.append(self.char_to_idx[token])

        return tokens

    def decode(self, tokens):
        """Декодирует индексы в текст"""
        # Преобразуем индексы в токены
        text_tokens = []
        for t in tokens:
            if t in self.idx_to_char:
                text_tokens.append(self.idx_to_char[t])
            else:
                text_tokens.append('?')

        # Объединяем в текст
        return ''.join(text_tokens)


# Создаем токенизатор
print("Создание BPE токенизатора...")

# Загружаем текст
if not os.path.exists('data.txt'):
    print("Создаю data.txt...")
    with open('data.txt', 'w', encoding='utf-8') as f:
        f.write("Привет мир! Это тестовый текст. " * 100)

with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Обучаем токенизатор
tokenizer = SimpleBPETokenizer()
tokenizer.train(text, vocab_size=1000)

# Сохраняем
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

print(f"✅ Токенизатор сохранен в tokenizer.pkl")
print(f"   Размер файла: {os.path.getsize('tokenizer.pkl')} байт")

# Тестируем
test_text = "Привет мир"
encoded = tokenizer.encode(test_text)
decoded = tokenizer.decode(encoded)
print(f"\nТест:")
print(f"  Исходный: {test_text}")
print(f"  Закодировано: {encoded[:20]}...")
print(f"  Декодировано: {decoded}")