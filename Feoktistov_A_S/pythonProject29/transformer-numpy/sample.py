# sample.py
import numpy as np
import pickle
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True, help='Prompt text')
    parser.add_argument('--tokens', type=int, default=100, help='Number of tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=40, help='Top-k sampling')
    parser.add_argument('--model', type=str, default='model.pkl', help='Model file')

    args = parser.parse_args()

    # Загружаем модель
    with open(args.model, 'rb') as f:
        model = pickle.load(f)

    # Загружаем токенизатор (вам нужно реализовать)
    # tokenizer = load_tokenizer()

    # Токенизируем промпт
    # prompt_tokens = tokenizer.encode(args.prompt)

    # Для теста используем случайные токены
    prompt_tokens = np.random.randint(0, model.vocab_size, 20)

    # Генерируем
    generated = model.generate(
        prompt_tokens,
        max_new_tokens=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k
    )

    # Декодируем
    # generated_text = tokenizer.decode(generated)
    # print(generated_text)

    print("Generated tokens:", generated)


if __name__ == "__main__":
    main()