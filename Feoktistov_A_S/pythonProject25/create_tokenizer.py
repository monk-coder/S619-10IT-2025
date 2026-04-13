
import pickle
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tokenizer_class import FreshTokenizer

print("="*60)
print("СОЗДАНИЕ ТОКЕНИЗАТОРА")
print("="*60)

if not os.path.exists('data.txt'):
    print("\n❌ data.txt не найден!")
    print("Создаю тестовый data.txt...")
    with open('data.txt', 'w', encoding='utf-8') as f:
        f.write("Привет мир! Это тестовый текст для обучения. " * 200)
    print("✅ data.txt создан")

print("\nЗагрузка текста...")
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Загружено {len(text)} символов")
print(f"Первые 100 символов: {text[:100]}")

print("\nОбучение токенизатора...")
tokenizer = FreshTokenizer()
tokenizer.train(text, max_vocab=1000)

print(f"Размер словаря: {tokenizer.vocab_size}")

print("\nСохранение токенизатора...")
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

print(f"✅ Токенизатор сохранен в tokenizer.pkl")
print(f"   Размер файла: {os.path.getsize('tokenizer.pkl')} байт")

test_text = "Привет"
encoded = tokenizer.encode(test_text)
decoded = tokenizer.decode(encoded)
print(f"\nТест:")
print(f"  '{test_text}' -> {encoded} -> '{decoded}'")

print("\n✅ Готово!")
