import numpy as np
import pickle
import argparse
import os
from model import TransformerLM


def top_k_sampling(logits, k=50, temperature=1.0):
    logits = logits / temperature

    # Top-k фильтрация
    if k > 0:
        indices = np.argpartition(logits, -k)[-k:]
        mask = np.zeros_like(logits)
        mask[indices] = 1
        logits = logits * mask + (1 - mask) * (-1e9)

    # Softmax
    probs = np.exp(logits - np.max(logits))
    probs = probs / np.sum(probs)

    # Сэмплирование
    return np.random.choice(len(probs), p=probs)


def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=0.8, top_k=40):
    # Кодирование промпта
    input_ids = tokenizer.encode(prompt)
    input_ids = np.array(input_ids[-model.max_seq_len:])  # Обрезаем до максимальной длины

    generated = input_ids.tolist()

    for _ in range(max_new_tokens):
        # Подготовка входа
        x = np.array([generated[-model.max_seq_len:]])  # Берем последние токены

        # Forward pass
        logits = model.forward(x)

        # Получаем логиты для последнего токена
        next_token_logits = logits[0, -1, :]

        # Сэмплируем следующий токен
        next_token = top_k_sampling(next_token_logits, k=top_k, temperature=temperature)

        generated.append(next_token)

        # Проверяем на конец последовательности
        decoded = tokenizer.decode([next_token])
        if decoded == '<EOS>' or decoded == '':
            break

    return tokenizer.decode(generated)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default='The future of AI')
    parser.add_argument('--max_tokens', type=int, default=50)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=40)
    args = parser.parse_args()

    # Проверка наличия файлов модели
    if not os.path.exists('model_params.npz') or not os.path.exists('tokenizer.pkl'):
        print("Model files not found. Please run train.py first.")
        return

    # Загрузка модели
    print("Loading model...")
    model = TransformerLM(
        vocab_size=500,
        d_model=128,
        n_head=2,
        n_layer=2,
        d_ff=256,
        max_seq_len=64
    )

    # Загрузка параметров
    params_data = np.load('model_params.npz')
    model_params = model.parameters()
    for i, (key, value) in enumerate(params_data.items()):
        if i < len(model_params):
            model_params[i][:] = value

    # Загрузка токенизатора
    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    # Генерация для нескольких промптов
    prompts = [args.prompt, "Machine learning", "Neural networks"]

    for prompt in prompts:
        print(f"\n{'=' * 50}")
        print(f"Prompt: {prompt}")
        print(f"{'=' * 50}")

        generated_text = generate(
            model, tokenizer,
            prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )

        print(f"Generated: {generated_text}")
        print()


if __name__ == '__main__':
    main()