# sample.py
import numpy as np
import argparse
import pickle
import sys
import os

def stable_softmax_1d(x):
    x_max = np.max(x)
    exp_x = np.exp(x - x_max)
    return exp_x / (np.sum(exp_x) + 1e-9)

def sample_token(logits, temperature=1.0, top_k=50):
    logits = np.array(logits, dtype=np.float64).copy()
    if temperature > 0:
        logits = logits / temperature
    if top_k > 0 and top_k < len(logits):
        kth_val = np.partition(logits, -top_k)[-top_k]
        logits[logits < kth_val] = -1e9
    probs = stable_softmax_1d(logits)
    return np.random.choice(len(probs), p=probs)

def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=1.0, top_k=50):
    context = tokenizer.encode(prompt)
    if len(context) == 0:
        # Фоллбэк, если prompt не токенизировался
        context = [tokenizer.token_to_id.get(tokenizer.id_to_token[0], 0)]
        
    context = np.array(context, dtype=np.int32)
    model.training = False  # Отключаем dropout

    for _ in range(max_new_tokens):
        if len(context) > model.max_seq_len:
            context = context[-model.max_seq_len:]
            
        x = context.reshape(1, -1)
        logits = model.forward(x)  # (1, T, vocab_size)
        
        next_logits = logits[0, -1]
        next_token = sample_token(next_logits, temperature, top_k)
        context = np.append(context, next_token)
        
    return tokenizer.decode(context.tolist())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='checkpoints/model.pkl')
    parser.add_argument('--prompt', type=str, default='the cat')
    parser.add_argument('--max_tokens', type=int, default=60)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    np.random.seed(args.seed)

    if not os.path.exists(args.model):
        print(f"❌ Модель не найдена: {args.model}")
        print("Сначала запустите train.py")
        sys.exit(1)

    print(f"📦 Загрузка модели...")
    with open(args.model, 'rb') as f:
        data = pickle.load(f)
    model = data['model']
    tokenizer = data['tokenizer']

    print(f"🔤 Генерация: prompt='{args.prompt}', temp={args.temperature}, top_k={args.top_k}")
    result = generate(model, tokenizer, args.prompt, args.max_tokens, args.temperature, args.top_k)

    print("\n" + "="*60)
    print(f"📝 Prompt:    {args.prompt}")
    print(f"🤖 Generated: {result}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()