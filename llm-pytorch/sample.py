"""
Простая генерация текста - РАБОЧАЯ ВЕРСИЯ
"""

import torch
import os

# Добавляем путь к текущей папке
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model import GPTLanguageModel

def main():
    print("🎨 ГЕНЕРАЦИЯ ТЕКСТА")
    print("="*60)
    
    # ПАРАМЕТРЫ (меняйте здесь что нужно)
    CHECKPOINT_PATH = 'checkpoints/best_model.pt'
    PROMPT = "ROMEO:"
    MAX_NEW_TOKENS = 100
    TEMPERATURE = 0.8
    TOP_K = 40
    
    # Выбираем устройство
    if torch.cuda.is_available():
        DEVICE = 'cuda'
    elif torch.backends.mps.is_available():
        DEVICE = 'mps'
    else:
        DEVICE = 'cpu'
    
    print(f"Устройство: {DEVICE}")
    print(f"Чекпоинт: {CHECKPOINT_PATH}")
    print(f"Промпт: {PROMPT}")
    print("="*60)
    
    # ПРОВЕРКА: существует ли файл с моделью
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"\n❌ ОШИБКА: Файл {CHECKPOINT_PATH} не найден!")
        print("\n📌 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
        print("1. Сначала обучите модель командой: python train.py")
        print("2. Или создайте тестовую модель (см. инструкцию ниже)")
        print("3. Или укажите другой путь к чекпоинту")
        
        # Спрашиваем, хочет ли пользователь создать тестовую модель
        answer = input("\nСоздать тестовую модель для проверки? (y/n): ")
        if answer.lower() == 'y':
            create_test_model()
            print("\n✅ Тестовая модель создана! Запустите скрипт еще раз.")
        return
    
    try:
        # Загружаем чекпоинт
        print("\n📦 Загрузка модели...")
        checkpoint = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
        
        # Определяем размеры модели из чекпоинта
        if 'args' in checkpoint:
            n_embd = checkpoint['args'].n_embd
            n_head = checkpoint['args'].n_head
            n_layer = checkpoint['args'].n_layer
            block_size = checkpoint['args'].block_size
            vocab_size = checkpoint['args'].vocab_size
        else:
            # Используем стандартные размеры, как в train.py
            print("⚠️ Использую стандартные размеры модели (128, 4, 4)")
            n_embd = 128
            n_head = 4
            n_layer = 4
            block_size = 128
            vocab_size = 65  # Стандартный размер для ASCII символов
        
        print(f"Размеры модели: emb={n_embd}, heads={n_head}, layers={n_layer}")
        
        # Создаем модель с теми же размерами, что при обучении
        model = GPTLanguageModel(
            vocab_size=vocab_size,
            n_embd=n_embd,
            n_head=n_head,
            n_layer=n_layer,
            block_size=block_size,
            dropout=0  # Выключаем dropout для генерации
        ).to(DEVICE)
        
        # Загружаем веса
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model.eval()
        print("✅ Модель загружена успешно!")
        
        # Генерируем текст
        print("\n🎬 Генерация текста...\n")
        print(f"Промпт: {PROMPT}")
        print("-"*60)
        
        # Простая character-level токенизация
        # Собираем все символы из текста (нужно для обратного преобразования)
        chars = []
        if 'stoi' in checkpoint:
            chars = list(checkpoint['stoi'].keys())
        else:
            # Создаем базовый набор символов
            chars = [chr(i) for i in range(32, 127)]  # ASCII от пробела до ~
            chars.append('\n')
        
        stoi = {ch: i for i, ch in enumerate(chars)}
        itos = {i: ch for i, ch in enumerate(chars)}
        
        # Кодируем промпт
        context = torch.tensor([stoi.get(ch, 0) for ch in PROMPT], dtype=torch.long).unsqueeze(0).to(DEVICE)
        
        # Генерируем пошагово
        generated = context.clone()
        for _ in range(MAX_NEW_TOKENS):
            # Берем последние block_size токенов
            context_cut = generated[:, -block_size:]
            
            # Получаем предсказания
            with torch.no_grad():
                logits, _ = model(context_cut)
            
            # Берем последний токен
            logits = logits[0, -1, :] / TEMPERATURE
            
            # Top-k фильтрация
            if TOP_K > 0:
                top_k_values, top_k_indices = torch.topk(logits, min(TOP_K, logits.size(-1)))
                mask = torch.ones_like(logits) * float('-inf')
                mask[top_k_indices] = top_k_values
                logits = mask
            
            # Преобразуем в вероятности и семплируем
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            # Добавляем к результату
            generated = torch.cat((generated, next_token.unsqueeze(0)), dim=1)
            
            # Печатаем текущий символ
            char = itos.get(next_token.item(), '?')
            print(char, end='', flush=True)
        
        print("\n" + "-"*60)
        print("\n✅ Генерация завершена!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n📌 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. Модель не обучена или обучена с другими параметрами")
        print("2. Несовместимость версий PyTorch")
        print("3. Поврежденный файл чекпоинта")
        
        print("\n📌 РЕШЕНИЕ: Обучите модель заново")
        print("   Запустите: python train.py")
        print("   Затем снова: python sample.py")

def create_test_model():
    """Создает тестовую модель для проверки"""
    print("\n🔧 Создание тестовой модели...")
    
    from model import GPTLanguageModel
    import torch
    
    # Создаем маленькую модель
    model = GPTLanguageModel(
        vocab_size=65,  # ASCII символы
        n_embd=64,
        n_head=4,
        n_layer=4,
        block_size=128,
        dropout=0.1
    )
    
    # Сохраняем
    os.makedirs('checkpoints', exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'args': type('Args', (), {
            'n_embd': 64,
            'n_head': 4, 
            'n_layer': 4,
            'block_size': 128,
            'vocab_size': 65
        })()
    }, 'checkpoints/best_model.pt')
    
    print("✅ Тестовая модель создана в checkpoints/best_model.pt")

if __name__ == "__main__":
    main()
