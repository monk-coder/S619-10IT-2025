# setup_complete.py
import pickle
import os
import sys


# Определяем класс
class SimpleBPETokenizer:
    def __init__(self):
        self.vocab_size = 0
        self.char_to_idx = {}
        self.idx_to_char = {}

    def train_from_text(self, text, vocab_size=1000):
        chars = sorted(list(set(text)))
        self.vocab_size = min(vocab_size, len(chars))
        self.char_to_idx = {ch: i for i, ch in enumerate(chars[:self.vocab_size])}
        self.idx_to_char = {i: ch for i, ch in enumerate(chars[:self.vocab_size])}
        return self

    def encode(self, text):
        return [self.char_to_idx.get(ch, 0) for ch in text]

    def decode(self, tokens):
        return ''.join([self.idx_to_char.get(t, '?') for t in tokens])


def setup():
    print("Полная переустановка...")

    # Удаляем старые файлы
    if os.path.exists('tokenizer.pkl'):
        os.remove('tokenizer.pkl')
        print("Удален старый tokenizer.pkl")

    # Создаем data.txt если нет
    if not os.path.exists('data.txt'):
        with open('data.txt', 'w', encoding='utf-8') as f:
            f.write("Привет мир! Это тестовый текст для обучения. " * 200)
        print("Создан data.txt")

    # Создаем токенизатор
    with open('data.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    tokenizer = SimpleBPETokenizer()
    tokenizer.train_from_text(text, vocab_size=1000)

    with open('tokenizer.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)

    print(f"✅ Токенизатор создан! Размер словаря: {tokenizer.vocab_size}")
    print(f"   Размер файла: {os.path.getsize('tokenizer.pkl')} байт")

    # Тестируем загрузку
    print("\nТестируем загрузку...")
    with open('tokenizer.pkl', 'rb') as f:
        test = pickle.load(f)

    test_text = "Привет"
    encoded = test.encode(test_text)
    decoded = test.decode(encoded)
    print(f"   Тест: '{test_text}' -> {encoded} -> '{decoded}'")

    print("\n✅ Готово! Теперь запускайте train.py")


if __name__ == "__main__":
    setup()