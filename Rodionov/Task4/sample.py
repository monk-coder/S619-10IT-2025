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


def load_latest_model(model_class, model_params):
    """Загружает последнюю сохраненную модель"""
    models_dir = 'models'
    if not os.path.exists(models_dir):
        print(f"Directory {models_dir} not found. Please run train.py first.")
        return None, None

    # Ищем файлы модели
    model_files = [f for f in os.listdir(models_dir) if f.startswith('model_params_') and f.endswith('.npz')]
    tokenizer_files = [f for f in os.listdir(models_dir) if f.startswith('tokenizer_') and f.endswith('.pkl')]

    if not model_files or not tokenizer_files:
        # Пробуем загрузить latest
        latest_model = os.path.join(models_dir, 'model_params_latest.npz')
        latest_tokenizer = os.path.join(models_dir, 'tokenizer_latest.pkl')

        if os.path.exists(latest_model) and os.path.exists(latest_tokenizer):
            model = model_class(**model_params)
            params_data = np.load(latest_model)
            model_params_list = model.parameters()
            for i, (key, value) in enumerate(params_data.items()):
                if i < len(model_params_list):
                    model_params_list[i][:] = value

            with open(latest_tokenizer, 'rb') as f:
                tokenizer = pickle.load(f)

            print("Loaded latest model and tokenizer")
            return model, tokenizer
        else:
            return None, None

    # Находим самый свежий файл по дате в имени
    latest_model = sorted(model_files)[-1]
    latest_tokenizer = sorted(tokenizer_files)[-1]

    model_path = os.path.join(models_dir, latest_model)
    tokenizer_path = os.path.join(models_dir, latest_tokenizer)

    # Загружаем модель
    model = model_class(**model_params)
    params_data = np.load(model_path)
    model_params_list = model.parameters()
    for i, (key, value) in enumerate(params_data.items()):
        if i < len(model_params_list):
            model_params_list[i][:] = value

    with open(tokenizer_path, 'rb') as f:
        tokenizer = pickle.load(f)

    print(f"Loaded model from {latest_model}")
    print(f"Loaded tokenizer from {latest_tokenizer}")

    return model, tokenizer


def load_metrics():
    """Загружает метрики обучения"""
    models_dir = 'models'
    metrics_files = [f for f in os.listdir(models_dir) if f.startswith('metrics_') and f.endswith('.pkl')]

    if not metrics_files:
        return None

    latest_metrics = sorted(metrics_files)[-1]
    metrics_path = os.path.join(models_dir, latest_metrics)

    with open(metrics_path, 'rb') as f:
        metrics = pickle.load(f)

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default='The future of AI')
    parser.add_argument('--max_tokens', type=int, default=50)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=40)
    parser.add_argument('--use_best', action='store_true', help='Use best model instead of latest')
    args = parser.parse_args()

    # Параметры модели
    model_params = {
        'vocab_size': 500,
        'd_model': 128,
        'n_head': 2,
        'n_layer': 2,
        'd_ff': 256,
        'max_seq_len': 64
    }

    # Загрузка метрик обучения
    metrics = load_metrics()
    if metrics:
        print("\n=== Training Metrics ===")
        print(f"Final Train Accuracy: {metrics['train_accuracies'][-1]:.4f}")
        print(f"Final Validation Accuracy: {metrics['val_accuracies'][-1]:.4f}")
        print(f"Best Validation Accuracy: {metrics.get('best_val_accuracy', 'N/A')}")
        print(f"Final Train Loss: {metrics['train_losses'][-1]:.4f}")
        print(f"Final Validation Loss: {metrics['val_losses'][-1]:.4f}")
        print("========================\n")

    # Загрузка модели
    print("Loading model...")

    if args.use_best:
        # Загрузка лучшей модели
        best_model_path = os.path.join('models', 'best_model.npz')
        if os.path.exists(best_model_path):
            model = TransformerLM(**model_params)
            params_data = np.load(best_model_path)
            model_params_list = model.parameters()
            for i, (key, value) in enumerate(params_data.items()):
                if i < len(model_params_list):
                    model_params_list[i][:] = value

            # Загружаем токенизатор
            tokenizer_files = [f for f in os.listdir('models') if f.startswith('tokenizer_')]
            if tokenizer_files:
                latest_tokenizer = sorted(tokenizer_files)[-1]
                with open(os.path.join('models', latest_tokenizer), 'rb') as f:
                    tokenizer = pickle.load(f)
                print("Loaded best model")
            else:
                print("Tokenizer not found")
                return
        else:
            print("Best model not found, loading latest...")
            model, tokenizer = load_latest_model(TransformerLM, model_params)
    else:
        model, tokenizer = load_latest_model(TransformerLM, model_params)

    if model is None or tokenizer is None:
        print("Model files not found. Please run train.py first.")
        return

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