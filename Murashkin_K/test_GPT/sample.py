import argparse
import pickle
import numpy as np
from model import TransformerLM

def generate(model, prompt_indices, max_new_tokens, max_len, temperature=1.0, top_k=None):
    """
    Генерация последовательности токенов на основе входного промпта.
    """
    generated = list(prompt_indices)

    for _ in range(max_new_tokens):
        context = generated[-max_len:]
        x = np.array([context], dtype=np.int32)


        logits = model.forward(x)

        next_token_logits = logits[0, -1, :] / max(temperature, 1e-5)

        if top_k is not None and top_k > 0:
            top_k = min(top_k, len(next_token_logits))
            threshold = np.partition(next_token_logits, -top_k)[-top_k]
            next_token_logits[next_token_logits < threshold] = -1e9

        max_logits = np.max(next_token_logits)
        probs = np.exp(next_token_logits - max_logits)
        probs /= (np.sum(probs) + 1e-15)

        next_token = np.random.choice(len(probs), p=probs)
        generated.append(next_token)

    return generated

def main():
    parser = argparse.ArgumentParser(description="NumPy GPT-style Text Generation Script")
    parser.add_argument("--prompt", type=str, required=True, help="Начальный текст (затравка) для генерации")
    parser.add_argument("--max_new_tokens", type=int, default=50, help="Количество генерируемых токенов")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Температура сэмплинга (0.1 - строго, 1.5 - хаотично)")
    parser.add_argument("--top_k", type=int, default=10,
                        help="Количество лучших токенов для отсечения хвоста распределения")
    parser.add_argument("--model_path", type=str, default="model_weights.pkl",
                        help="Путь к сохраненному файлу весов модели")
    args = parser.parse_args()

    print(f"Загрузка чекпоинта модели из '{args.model_path}'...")
    try:
        with open(args.model_path, "rb") as f:
            checkpoint = pickle.load(f)
    except FileNotFoundError:
        print(f"\n[Ошибка]: Файл весов '{args.model_path}' не найден!")
        print("Пожалуйста, убедитесь, что вы сначала запустили обучение через 'train.py' и веса сохранились.")
        return

    config = checkpoint["config"]
    char_to_idx = checkpoint["char_to_idx"]
    idx_to_char = checkpoint["idx_to_char"]

    print("Инициализация структуры TransformerLM...")
    model = TransformerLM(
        vocab_size=config["vocab_size"],
        max_len=config["max_len"],
        d_model=config["d_model"],
        n_head=config["n_head"],
        n_layer=config["n_layer"],
        d_ff=config["d_ff"]
    )

    print("Загрузка матриц весов в слои сети...")
    weights = checkpoint["weights"]

    model.token_emb.weight = weights["token_emb.weight"]
    model.pos_emb.weight = weights["pos_emb.weight"]
    model.lm_head = weights["lm_head"]
    model.ln_f.gamma = weights["ln_f.gamma"]
    model.ln_f.beta = weights["ln_f.beta"]

    for i, block in enumerate(model.blocks):
        block.ln1.gamma = weights[f"block_{i}.ln1.gamma"]
        block.ln1.beta = weights[f"block_{i}.ln1.beta"]
        block.attn.W_q = weights[f"block_{i}.attn.W_q"]
        block.attn.W_k = weights[f"block_{i}.attn.W_k"]
        block.attn.W_v = weights[f"block_{i}.attn.W_v"]
        block.attn.W_o = weights[f"block_{i}.attn.W_o"]
        block.ln2.gamma = weights[f"block_{i}.ln2.gamma"]
        block.ln2.beta = weights[f"block_{i}.ln2.beta"]
        block.mlp.W1 = weights[f"block_{i}.mlp.W1"]
        block.mlp.b1 = weights[f"block_{i}.mlp.b1"]
        block.mlp.W2 = weights[f"block_{i}.mlp.W2"]
        block.mlp.b2 = weights[f"block_{i}.mlp.b2"]

    print("Модель успешно собрана и готова к работе.")

    prompt_indices = []
    for ch in args.prompt:
        if ch in char_to_idx:
            prompt_indices.append(char_to_idx[ch])
        else:

            prompt_indices.append(0)

    if len(prompt_indices) == 0:
        print("[Ошибка]: Входной промпт пустой или не содержит известных символов.")
        return

    print(f"\n=== Входной промпт: '{args.prompt}' ===")
    print(f"Индексы токенов: {prompt_indices}")
    print(f"Запуск генерации ({args.max_new_tokens} токенов, temp={args.temperature}, top_k={args.top_k})...")

    generated_indices = generate(
        model=model,
        prompt_indices=prompt_indices,
        max_new_tokens=args.max_new_tokens,
        max_len=config["max_len"],
        temperature=args.temperature,
        top_k=args.top_k
    )


    generated_text = "".join([idx_to_char[idx] for idx in generated_indices])

    print("\n================ ТЕКСТ ИЗ ВАШЕЙ LLM ================")
    print(generated_text)
    print("====================================================\n")


if __name__ == "__main__":
    main()
