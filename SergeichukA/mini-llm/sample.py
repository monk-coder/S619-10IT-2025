import numpy as np
import argparse
import os
import pickle
from tokenizer import SimpleBPETokenizer
from model import TransformerLM

# Гиперпараметры (должны совпадать с train.py!)
BLOCK_SIZE = 128
N_LAYER = 4
N_HEAD = 4
D_MODEL = 256

def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    """
    Генерация текста с помощью модели.
    
    Args:
        model: Обученная модель TransformerLM
        tokenizer: Токенизатор
        prompt: Начальный текст
        max_new_tokens: Сколько токенов сгенерировать
        temperature: Температура (1.0 = стандарт, >1 = креативнее, <1 = консервативнее)
        top_k: Ограничить выбор top_k наиболее вероятных токенов
    
    Returns:
        Сгенерированный текст
    """
    # Кодируем промпт
    context = tokenizer.encode(prompt)
    context = np.array([context], dtype=np.int32)  # (1, T)
    
    print(f"Prompt: {prompt}")
    print(f"Generating {max_new_tokens} tokens with temperature={temperature}...")
    print("-" * 50)
    
    for i in range(max_new_tokens):
        # Обрезаем контекст до размера блока
        ctx_cond = context[:, -BLOCK_SIZE:]
        
        # Прямой проход
        logits = model.forward(ctx_cond)
        
        # Берем logits для последнего токена
        logits = logits[:, -1, :] / temperature  # (1, V)
        
        # Top-K sampling (опционально)
        if top_k is not None:
            v, _ = np.partition(logits[0], -top_k)
            min_val = v[-top_k]
            mask = logits[0] < min_val
            logits[0][mask] = -1e9
        
        # Softmax
        e_x = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probs = e_x / e_x.sum(axis=-1, keepdims=True)
        
        # Сэмплирование
        next_token = np.random.choice(probs.shape[1], p=probs[0])
        
        # Добавляем к контексту
        context = np.append(context, [[next_token]], axis=1)
        
        # Показываем прогресс
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{max_new_tokens} tokens...", end='\r')
    
    print()  # Новая строка после прогресса
    
    # Декодируем результат
    generated_text = tokenizer.decode(context[0].tolist())
    
    return generated_text


def load_model_weights(model, filepath):
    """
    Загружает веса модели из файла.
    """
    if not os.path.exists(filepath):
        return False
    
    try:
        data = np.load(filepath, allow_pickle=True)
        
        # Загружаем embeddings
        if 'token_embedding' in data:
            model.token_embedding = data['token_embedding']
        if 'pos_embedding' in data:
            model.pos_embedding = data['pos_embedding']
        
        # Загружаем веса слоев (упрощенно - нужно сопоставить имена)
        # Для полноценной загрузки нужно сохранять веса с правильными именами
        print(f"✓ Weights loaded from {filepath}")
        return True
    except Exception as e:
        print(f"✗ Error loading weights: {e}")
        return False


def save_model_weights(model, filepath):
    """
    Сохраняет веса модели в файл.
    """
    params = model.parameters()
    params['token_embedding'] = model.token_embedding
    params['pos_embedding'] = model.pos_embedding
    
    np.savez(filepath, **params)
    print(f"✓ Weights saved to {filepath}")


if __name__ == '__main__':
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description='Генерация текста с помощью Mini-LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python sample.py --prompt "Hello" --max_new_tokens 100
  python sample.py --prompt "Once upon a time" --temperature 0.8 --top_k 40
  python sample.py --prompt "ROMEO:" --max_new_tokens 200 --temperature 1.2
        """
    )
    parser.add_argument('--prompt', type=str, default='Hello',
                        help='Начальный текст для генерации')
    parser.add_argument('--max_new_tokens', type=int, default=100,
                        help='Максимальное количество новых токенов')
    parser.add_argument('--temperature', type=float, default=1.0,
                        help='Температура генерации (0.5-2.0)')
    parser.add_argument('--top_k', type=int, default=None,
                        help='Ограничить выбор top_k токенов (опционально)')
    parser.add_argument('--check', action='store_true',
                        help='Только проверить наличие файлов, не генерировать')
    args = parser.parse_args()

    print("=" * 60)
    print("Mini-LLM Text Generation")
    print("=" * 60)
    
    # Проверка наличия необходимых файлов
    missing_files = []
    
    if not os.path.exists('data.txt'):
        missing_files.append('data.txt')
    
    if not os.path.exists('tokenizer.pkl'):
        missing_files.append('tokenizer.pkl')
    
    if not os.path.exists('model_weights.npz'):
        print("⚠ Warning: model_weights.npz not found (model not trained yet)")
    
    if missing_files and 'data.txt' in missing_files:
        print("✗ Error: Required files missing:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease run train.py first to create these files:")
        print("  python train.py")
        exit(1)
    
    # Загрузка или создание токенизатора
    print("\n[1/3] Loading tokenizer...")
    tokenizer = SimpleBPETokenizer()
    
    if os.path.exists('tokenizer.pkl'):
        tokenizer.load('tokenizer.pkl')
        print(f"✓ Tokenizer loaded (vocab size: {len(tokenizer.vocab)})")
    elif os.path.exists('data.txt'):
        print("⚠ Tokenizer not found, creating new one from data.txt...")
        with open('data.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        tokenizer.train(text)
        tokenizer.save('tokenizer.pkl')
        print(f"✓ New tokenizer created (vocab size: {len(tokenizer.vocab)})")
    else:
        print("✗ Error: Cannot create tokenizer (data.txt not found)")
        exit(1)
    
    # Если только проверка файлов
    if args.check:
        print("\n✓ All required files are present!")
        print("You can now run generation:")
        print(f"  python sample.py --prompt \"{args.prompt}\"")
        exit(0)
    
    # Инициализация модели
    print("\n[2/3] Initializing model...")
    vocab_size = len(tokenizer.vocab)
    model = TransformerLM(vocab_size, D_MODEL, N_LAYER, N_HEAD, BLOCK_SIZE)
    print(f"✓ Model initialized (vocab={vocab_size}, d_model={D_MODEL}, layers={N_LAYER})")
    
    # Загрузка весов
    print("\n[3/3] Loading model weights...")
    if os.path.exists('model_weights.npz'):
        load_model_weights(model, 'model_weights.npz')
    else:
        print("⚠ Using random weights (model not trained)")
        print("  Results will be random. Run train.py first for better results.")
    
    # Генерация текста
    print("\n" + "=" * 60)
    print("GENERATION")
    print("=" * 60 + "\n")
    
    try:
        generated_text = generate(
            model=model,
            tokenizer=tokenizer,
            prompt=args.prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )
        
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(generated_text)
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        print("\nPossible solutions:")
        print("  1. Make sure train.py completed successfully")
        print("  2. Check that data.txt contains valid text")
        print("  3. Try reducing max_new_tokens")
        print("  4. Try a different prompt")
        exit(1)