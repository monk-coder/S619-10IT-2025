import numpy as np
import pickle
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="")
    parser.add_argument('--tokens', type=int, default=50)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=40)
    args = parser.parse_args()

    # Загружаем модель
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)

    # Для теста - случайный промпт
    prompt = np.random.randint(0, model.vocab_size, 10)

    # Генерируем
    generated = model.generate(prompt, args.tokens, args.temperature, args.top_k)
    print("Generated tokens:", generated)


if __name__ == "__main__":
    main()