# make_tokenizer.py
import os
import sys
from tokenizer import BPETokenizer

def main():
    # Пути
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'data.txt')
    tokenizer_path = os.path.join(script_dir, 'tokenizer.pkl')
    
    # Проверка данных
    if not os.path.exists(data_path):
        print(f"❌ Data file not found: {data_path}")
        print("💡 Создайте data.txt с текстом для обучения")
        sys.exit(1)
    
    # Чтение текста
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    if len(text) < 100:
        print(f"❌ Data file too small: {len(text)} chars")
        print("💡 Добавьте больше текста в data.txt (минимум 1000 символов)")
        sys.exit(1)
    
    # Обучение токенизатора
    print(f"📚 Training tokenizer on {len(text)} characters...")
    tokenizer = BPETokenizer(vocab_size=500)  # Уменьшите до 200-300 для маленьких датасетов
    tokenizer.train(text)
    
    # Сохранение
    tokenizer.save(tokenizer_path)
    
    # Тест
    test_text = "Hello, world!"
    encoded = tokenizer.encode(test_text)
    decoded = tokenizer.decode(encoded)
    print(f"🧪 Test: '{test_text}' → {encoded} → '{decoded}'")
    print(f"✅ Done! Vocab size: {tokenizer.vocab_len}")

if __name__ == '__main__':
    main()