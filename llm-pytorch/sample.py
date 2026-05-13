"""
Продвинутая генерация текста с temperature и top-k sampling
"""

import torch
import argparse
from model import GPTLanguageModel

def load_model(checkpoint_path, device):
    """Загрузка модели из чекпоинта"""
    print(f"📦 Загрузка модели из {checkpoint_path}")
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    args = checkpoint['args']
    
    # Создаем модель (vocab_size нужно знать)
    # Для простоты используем стандартные размеры
    model = GPTLanguageModel(
        vocab_size=10000,  # Должно соответствовать при обучении
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
        dropout=0  # Выключаем dropout при инференсе
    ).to(device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    return model, args

def encode_text(text, vocab_size=10000):
    """Простая кодировка текста в токены"""
    # Для production нужно использовать тот же токенизатор, что при обучении
    # Здесь упрощенная версия - character-level
    chars = list(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    
    tokens = [stoi.get(ch, 0) for ch in text]
    return torch.tensor(tokens, dtype=torch.long).unsqueeze(0)

def decode_tokens(tokens, vocab_size=10000):
    """Декодировка токенов в текст"""
    # Простая декодировка для character-level
    # В production нужно использовать BPE декодер
    return ''.join([chr(t % 128) for t in tokens])

def generate_text(model, prompt, max_new_tokens, temperature=0.8, top_k=50, device='cuda'):
    """Генерация текста с продвинутыми параметрами"""
    
    # Кодируем промпт
    context = encode_text(prompt)
    context = context.to(device)
    
    # Генерируем
    with torch.no_grad():
        generated = model.generate(
            context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k
        )
    
    # Декодируем
    generated_text = decode_tokens(generated[0].cpu().numpy())
    
    return generated_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--prompt', type=str, default="ROMEO:",
                        help='Prompt for generation')
    parser.add_argument('--max_new_tokens', type=int, default=200,
                        help='Number of tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Sampling temperature (higher = more random)')
    parser.add_argument('--top_k', type=int, default=50,
                        help='Top-k sampling (0 = no top-k)')
    parser.add_argument('--device', type=str, default='cuda',
                        help='Device to use')
    
    args = parser.parse_args()
    
    print("🎨 ГЕНЕРАЦИЯ ТЕКСТА")
    print("="*60)
    print(f"Промпт: {args.prompt}")
    print(f"Temperature: {args.temperature}")
    print(f"Top-k: {args.top_k}")
    print(f"Max tokens: {args.max_new_tokens}")
    print("="*60)
    
    # Загружаем модель
    model, _ = load_model(args.checkpoint, args.device)
    
    # Генерируем
    print("\n🎬 Генерация...\n")
    generated_text = generate_text(
        model,
        args.prompt,
        args.max_new_tokens,
        args.temperature,
        args.top_k,
        args.device
    )
    
    print("="*60)
    print("РЕЗУЛЬТАТ:")
    print("="*60)
    print(generated_text)
    print("="*60)

if __name__ == "__main__":
    main()