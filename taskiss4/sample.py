import numpy as np
import argparse
import pickle
from bpe_tokenizer import BPETokenizer
from model import TransformerLM

def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=1.0, top_k=None):
    """
    Генерация текста
    prompt: строка - начало текста
    max_new_tokens: сколько новых токенов сгенерировать
    temperature: температура для softmax (>1 - более случайно, <1 - более детерминированно)
    top_k: если задано, оставляем только k самых вероятных токенов
    """
    
    # Токенизация prompt
    input_ids = tokenizer.encode(prompt)
    input_ids = np.array([input_ids])  # (1, seq_len)
    
    generated = input_ids[0].tolist()
    
    for _ in range(max_new_tokens):
        # Подготовка входной последовательности
        current_seq = np.array([generated[-model.max_seq_len:]])  # берем последние max_seq_len токенов
        
        # Forward pass
        logits = model.forward(current_seq)
        
        # Берем логиты последнего токена
        next_token_logits = logits[0, -1, :] / temperature
        
        # Top-k фильтрация
        if top_k is not None and top_k > 0:
            indices = np.argsort(next_token_logits)[-top_k:]
            mask = np.ones_like(next_token_logits) * -1e9
            mask[indices] = 0
            next_token_logits = next_token_logits + mask
        
        # Softmax
        exp_logits = np.exp(next_token_logits - np.max(next_token_logits))
        probs = exp_logits / np.sum(exp_logits)
        
        # Сэмплирование
        next_token = np.random.choice(len(probs), p=probs)
        
        # Добавляем к сгенерированному тексту
        generated.append(next_token)
    
    # Декодирование
    generated_text = tokenizer.decode(generated)
    return generated_text

def load_model(model_path, vocab_size):
    """Загрузка модели из файла"""
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
    
    # Восстанавливаем модель из сохраненных данных
    if isinstance(data, dict) and 'model' in data:
        model = data['model']
    else:
        # Если сохранена только модель
        model = data
    
    return model

def main():
    parser = argparse.ArgumentParser(description='Генерация текста с помощью Transformer')
    parser.add_argument('--prompt', type=str, default='The universe', help='Начальный текст')
    parser.add_argument('--model', type=str, default='transformer_lm_final.pkl', help='Путь к модели')
    parser.add_argument('--tokenizer', type=str, default='bpe_tokenizer.json', help='Путь к токенизатору')
    parser.add_argument('--max_tokens', type=int, default=100, help='Максимальное количество новых токенов')
    parser.add_argument('--temperature', type=float, default=1.0, help='Температура (0.5-2.0)')
    parser.add_argument('--top_k', type=int, default=50, help='Top-k фильтрация')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ТЕКСТА")
    print("=" * 60)
    
    # Загрузка токенизатора
    print(f"\n1. Загрузка токенизатора из {args.tokenizer}...")
    tokenizer = BPETokenizer()
    tokenizer.load(args.tokenizer)
    
    # Загрузка модели
    print(f"\n2. Загрузка модели из {args.model}...")
    model = load_model(args.model, len(tokenizer.vocab))
    
    print(f"\n3. Генерация с параметрами:")
    print(f"   Prompt: '{args.prompt}'")
    print(f"   Max tokens: {args.max_tokens}")
    print(f"   Temperature: {args.temperature}")
    print(f"   Top-k: {args.top_k}")
    
    # Генерация
    generated = generate(
        model, 
        tokenizer, 
        args.prompt, 
        max_new_tokens=args.max_tokens,
        temperature=args.temperature,
        top_k=args.top_k
    )
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ:")
    print("=" * 60)
    print(generated)
    
    # Дополнительные примеры
    print("\n" + "=" * 60)
    print("ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ:")
    print("=" * 60)
    
    test_prompts = [
        "Artificial intelligence",
        "Climate change",
        "Space exploration"
    ]
    
    for prompt in test_prompts:
        print(f"\n--- Prompt: '{prompt}' ---")
        generated = generate(model, tokenizer, prompt, max_new_tokens=50, temperature=0.8, top_k=40)
        print(generated)

if __name__ == "__main__":
    main()