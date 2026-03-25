import numpy as np
import argparse

from config import Config
from bpe_tokenizer import BPETokenizer
from model import TransformerLM


def load_model(model_path, tokenizer, config):
    """Загрузка обученной модели"""
    model = TransformerLM(config)

    # Загрузка параметров
    params = np.load(model_path)
    model.token_embedding.W = params['token_embedding']
    model.pos_embedding.W = params['pos_embedding']
    model.lm_head.W = params['lm_head']
    model.lm_head.b = params['lm_head_bias']

    return model


def generate_text(model, tokenizer, prompt, config):
    """Генерация текста"""
    # Токенизация промпта
    prompt_tokens = tokenizer.encode(prompt)

    # Генерация
    generated_tokens = model.generate(
        prompt_tokens,
        config.max_new_tokens,
        config.temperature,
        config.top_k
    )

    # Декодирование
    generated_text = tokenizer.decode(generated_tokens)
    return generated_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="Once upon a time", help="Prompt for generation")
    parser.add_argument('--model_path', type=str, default='model_params.npz', help="Path to model parameters")
    parser.add_argument('--temperature', type=float, default=0.8, help="Sampling temperature")
    parser.add_argument('--top_k', type=int, default=40, help="Top-k sampling")
    parser.add_argument('--max_new_tokens', type=int, default=100, help="Maximum tokens to generate")

    args = parser.parse_args()

    # Конфигурация
    config = Config()
    config.temperature = args.temperature
    config.top_k = args.top_k
    config.max_new_tokens = args.max_new_tokens

    # Загрузка токенизатора (нужно обучить или загрузить)
    tokenizer = BPETokenizer()
    with open(config.data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer.train(text, num_merges=1000)
    config.vocab_size = len(tokenizer.vocab)

    # Загрузка модели
    print("Loading model...")
    model = load_model(args.model_path, tokenizer, config)

    # Генерация
    print(f"Prompt: {args.prompt}")
    generated = generate_text(model, tokenizer, args.prompt, config)
    print(f"Generated: {generated}")

    # Генерация нескольких примеров
    prompts = [
        "The future of AI is",
        "In the beginning",
        "Machine learning models"
    ]

    print("\n" + "=" * 50)
    print("More examples:")
    print("=" * 50)

    for prompt in prompts:
        generated = generate_text(model, tokenizer, prompt, config)
        print(f"\nPrompt: {prompt}")
        print(f"Generated: {generated[:200]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()