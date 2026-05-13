"""
Продвинутая генерация текста с temperature и top-k sampling
"""

import torch
import argparse
import os
from model import GPTLanguageModel

def load_model(checkpoint_path, device):
    """Загрузка модели из чекпоинта"""
    print(f"📦 Загрузка модели из {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        print(f"❌ Ошибка: файл {checkpoint_path} не найден!")
        print("💡 Сначала обучите модель: python train.py")
        exit(1)
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Загружаем аргументы, если они есть в чекпоинте
    if 'args' in checkpoint:
        args = checkpoint['args']
    else:
        # Создаем объект с аргументами по умолчанию
        class Args:
            pass
        args = Args()
        args.n_embd = 384
        args.n_head = 6
        args.n_layer = 6
        args.block_size = 256
    
    # Создаем модель
    model = GPTLanguageModel(
        vocab_size=10000,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
        dropout=0
    ).to(device)
    
    # Загружаем веса (если структура не совпадает, пробуем загрузить только то, что есть)
    try:
        model.load_state_dict(checkpoint['model_state_dict'])
    except:
        print("⚠️ Загружаем только совместимые веса...")
        model_dict = model.state_dict()
        pretrained_dict = {k: v for k, v in checkpoint['model_state_dict'].items() 
                          if k in model_dict and v.shape == model_dict[k].shape}
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)
    
    model.eval()
    return model, args

def encode_text(text, vocab_size=10000):
    """Простая кодировка текста в токены"""
    chars = list(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    tokens = [stoi.get(ch, 0) for ch in text]
    return torch.tensor(tokens, dtype=torch.long).unsqueeze(0)

def decode_tokens(tokens, vocab_size=10000):
    """Декодировка токенов в текст"""
    return ''.join([chr(t % 128) for t in tokens])

def generate_text(model, prompt, max_new_tokens, temperature=0.8, top_k=50, device='cuda'):
    """Генерация текста"""
    context = encode_text(prompt)
    context = context.to(device)
    
    with torch.no_grad():
        generated = model.generate(
            context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k
        )
    
    generated_text = decode_tokens(generated[0].cpu().numpy())
    return generated_text

def main():
    # ПРОВЕРКА: если нет аргументов, используем значения по умолчанию
    import sys
    
    # Значения по умолчанию
    default_values = {
        'checkpoint': 'checkpoints/best_model.pt',
        'prompt': 'ROMEO:',
        'max_new_tokens': 200,
        'temperature': 0.8,
        'top_k': 50,
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    }
    
    # Если аргументов нет или их меньше 2, используем значения по умолчанию
    if len(sys.argv) == 1:
        print("⚠️ Аргументы не указаны, использую значения по умолчанию!")
        print(f"   Проверьте: {default_values['checkpoint']}")
        print("   Для указания своих аргументов используйте:")
        print("   python sample.py --checkpoint=checkpoints/best_model.pt --prompt='ROMEO:'\n")
        
        checkpoint = default_values['checkpoint']
        prompt = default_values['prompt']
        max_new_tokens = default_values['max_new_tokens']
        temperature = default_values['temperature']
        top_k = default_values['top_k']
        device = default_values['device']
    else:
        # Парсим аргументы командной строки
        parser = argparse.ArgumentParser()
        parser.add_argument('--checkpoint', type=str, required=False, default='checkpoints/best_model.pt')
        parser.add_argument('--prompt', type=str, default="ROMEO:")
        parser.add_argument('--max_new_tokens', type=int, default=200)
        parser.add_argument('--temperature', type=float, default=0.8)
        parser.add_argument('--top_k', type=int, default=50)
        parser.add_argument('--device', type=str, default='cuda')
        args = parser.parse_args()
        
        checkpoint = args.checkpoint
        prompt = args.prompt
        max_new_tokens = args.max_new_tokens
        temperature = args.temperature
        top_k = args.top_k
        device = args.device
    
    print("🎨 ГЕНЕРАЦИЯ ТЕКСТА")
    print("="*60)
    print(f"Промпт: {prompt}")
    print(f"Temperature: {temperature}")
    print(f"Top-k: {top_k}")
    print(f"Max tokens: {max_new_tokens}")
    print(f"Чекпоинт: {checkpoint}")
    print("="*60)
    
    # Проверяем существование чекпоинта
    if not os.path.exists(checkpoint):
        print(f"\n❌ ОШИБКА: Файл {checkpoint} не найден!")
        print("\nЧто делать:")
        print("1. Сначала обучите модель: python train.py")
        print("2. Или укажите правильный путь к чекпоинту:")
        print("   python sample.py --checkpoint=checkpoints/final_model.pt")
        return
    
    # Загружаем модель
    model, _ = load_model(checkpoint, device)
    
    # Генерируем
    print("\n🎬 Генерация...\n")
    generated_text = generate_text(
        model,
        prompt,
        max_new_tokens,
        temperature,
        top_k,
        device
    )
    
    print("="*60)
    print("РЕЗУЛЬТАТ:")
    print("="*60)
    print(generated_text)
    print("="*60)

if __name__ == "__main__":
    main()
