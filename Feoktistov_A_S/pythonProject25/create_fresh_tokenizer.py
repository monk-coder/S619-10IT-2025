# create_fresh_tokenizer.py
import pickle
import os


class FreshTokenizer:
    """Простой рабочий токенизатор"""

    def __init__(self):
        self.vocab_size = 0
        self.char_to_idx = {}
        self.idx_to_char = {}

    def train(self, text, max_vocab=1000):
        """Обучает на тексте"""
        # Получаем все уникальные символы
        chars = sorted(list(set(text)))

        # Ограничиваем размер словаря
        self.vocab_size = min(max_vocab, len(chars))

        # Создаем отображения
        self.char_to_idx = {ch: i for i, ch in enumerate(chars[:self.vocab_size])}
        self.idx_to_char = {i: ch for i, ch in enumerate(chars[:self.vocab_size])}

        print(f"✅ Токенизатор обучен")
        print(f"   Всего символов: {len(chars)}")
        print(f"   Размер словаря: {self.vocab_size}")

        return self

    def encode(self, text):
        """Кодирует текст в индексы"""
        return [self.char_to_idx.get(ch, 0) for ch in text]

    def decode(self, tokens):
        """Декодирует индексы в текст"""
        return ''.join([self.idx_to_char.get(t, '?') for t in tokens])


print("=" * 60)
print("СОЗДАНИЕ НОВОГО ТОКЕНИЗАТОРА")
print("=" * 60)

# 1. Проверяем data.txt
if not os.path.exists('data.txt'):
    print("\n❌ data.txt не найден!")
    print("Создаю тестовый data.txt...")
    with open('data.txt', 'w', encoding='utf-8') as f:
        f.write("Привет мир! Это тестовый текст для обучения. " * 200)
    print("✅ data.txt создан")

# 2. Загружаем текст
print("\nЗагрузка текста...")
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Загружено {len(text)} символов")
print(f"Первые 100 символов: {text[:100]}")

# 3. Создаем токенизатор
print("\nОбучение токенизатора...")
tokenizer = FreshTokenizer()
tokenizer.train(text, max_vocab=1000)

# 4. Сохраняем
print("\nСохранение токенизатора...")
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

# 5. Проверяем
print("\nПроверка сохранения...")
if os.path.exists('tokenizer.pkl'):
    size = os.path.getsize('tokenizer.pkl')
    print(f"✅ Файл создан: tokenizer.pkl")
    print(f"   Размер: {size} байт")

    # Проверяем, что это файл, а не папка
    if os.path.isdir('tokenizer.pkl'):
        print("   ❌ Это папка, а не файл!")
    else:
        print("   ✅ Это файл")
else:
    print("❌ Файл не создан!")

# 6. Тестируем загрузку
print("\nТестирование загрузки...")
try:
    with open('tokenizer.pkl', 'rb') as f:
        test_tokenizer = pickle.load(f)

    print("✅ Токенизатор успешно загружен")
    print(f"   vocab_size: {test_tokenizer.vocab_size}")

    test_text = "Привет"
    encoded = test_tokenizer.encode(test_text)
    decoded = test_tokenizer.decode(encoded)
    print(f"   Тест encode/decode: '{test_text}' -> {encoded} -> '{decoded}'")

except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")

print("\n" + "=" * 60)
print("✅ ГОТОВО!")
print("=" * 60)
print("\nТеперь запускайте обучение:")
print("python train.py --batch_size=16 --max_iters=100 --device=cpu")