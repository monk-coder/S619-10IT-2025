# test_tokenizer.py
import pickle

try:
    with open('', 'rb') as f:
        tokenizer = pickle.load(f)

    print("✅ Токенизатор загружен")
    print(f"   vocab_size: {tokenizer.vocab_size}")

    test_text = "Привет мир"
    encoded = tokenizer.encode(test_text)
    print(f"   encode('{test_text}'): {encoded[:10]}...")

    decoded = tokenizer.decode(encoded)
    print(f"   decode(): {decoded[:50]}...")

except Exception as e:
    print(f"❌ Ошибка: {e}")