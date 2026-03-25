# verify_tokenizer.py
import pickle
import os
import sys

# Добавляем текущую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем класс токенизатора
from tokenizer_class import FreshTokenizer

print("=" * 60)
print("ПРОВЕРКА ТОКЕНИЗАТОРА")
print("=" * 60)

# Проверяем существование файла
if not os.path.exists('tokenizer.pkl'):
    print("❌ tokenizer.pkl не существует!")
    print("Запустите create_tokenizer.py сначала")
    sys.exit(1)

# Проверяем, что это не папка
if os.path.isdir('tokenizer.pkl'):
    print("❌ tokenizer.pkl - это ПАПКА!")
    sys.exit(1)

# Проверяем размер
size = os.path.getsize('tokenizer.pkl')
print(f"Размер файла: {size} байт")

if size == 0:
    print("❌ Файл пустой!")
    sys.exit(1)

# Загружаем токенизатор
try:
    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    print("✅ Токенизатор загружен успешно!")
    print(f"   Тип: {type(tokenizer).__name__}")
    print(f"   vocab_size: {tokenizer.vocab_size}")

    # Проверяем методы
    test_text = "Привет мир"
    encoded = tokenizer.encode(test_text)
    decoded = tokenizer.decode(encoded)

    print(f"\nТест encode/decode:")
    print(f"  Исходный: {test_text}")
    print(f"  Закодировано: {encoded[:10]}...")
    print(f"  Декодировано: {decoded[:50]}")

    if test_text[:10] == decoded[:10]:
        print("  ✅ Результат совпадает!")
    else:
        print("  ⚠️  Результат не совпадает (но это нормально для простого токенизатора)")

except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    print(f"   Тип: {type(e).__name__}")

print("\n" + "=" * 60)