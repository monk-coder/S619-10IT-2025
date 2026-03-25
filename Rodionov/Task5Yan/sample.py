import torch
import argparse
import os
import json

from model import GPT
from data import BPEEncoder


def get_args():
    parser = argparse.ArgumentParser(description='Генерация текста с помощью обученной модели')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Путь к чекпоинту модели')
    parser.add_argument('--prompt', type=str, default="ROMEO:",
                        help='Начальный промпт')
    parser.add_argument('--max_new_tokens', type=int, default=200,
                        help='Максимальное количество новых токенов')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Температура сэмплирования (1.0 = без изменений)')
    parser.add_argument('--top_k', type=int, default=50,
                        help='Top-k фильтрация (None = отключена)')
    parser.add_argument('--device', type=str, default='cuda',
                        help='Устройство для инференса')
    return parser.parse_args()


def main():
    args = get_args()

    # Проверяем наличие чекпоинта
    if not os.path.exists(args.checkpoint):
        print(f"❌ Ошибка: чекпоинт {args.checkpoint} не найден!")
        return

    # Загружаем чекпоинт
    checkpoint = torch.load(args.checkpoint, map_location=args.device)

    # Пытаемся загрузить параметры модели из отдельного файла
    checkpoint_dir = os.path.dirname(args.checkpoint)
    model_params_path = os.path.join(checkpoint_dir, 'model_params.json')

    if os.path.exists(model_params_path):
        with open(model_params_path, 'r') as f:
            model_params = json.load(f)
    else:
        # Параметры по умолчанию (должны совпадать с обучением)
        print("⚠️ Файл параметров модели не найден, используются значения по умолчанию")
        model_params = {
            'vocab_size': 5000,
            'embed_dim': 384,
            'num_heads': 6,
            'num_layers': 6,
            'block_size': 256
        }

    # Создаем модель
    print("Создание модели...")
    model = GPT(
        vocab_size=model_params['vocab_size'],
        embed_dim=model_params['embed_dim'],
        num_heads=model_params['num_heads'],
        num_layers=model_params['num_layers'],
        block_size=model_params['block_size']
    )

    # Загружаем веса
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(args.device)
    model.eval()
    print(f"✅ Модель загружена (шаг {checkpoint.get('step', 'unknown')})")

    # Загружаем энкодер
    encoder_path = os.path.join(checkpoint_dir, 'bpe_encoder.pt')
    encoder = BPEEncoder()

    if os.path.exists(encoder_path):
        encoder.load(encoder_path)
        print(f"✅ Энкодер загружен из {encoder_path}")
    else:
        print("❌ Ошибка: BPE энкодер не найден!")
        return

    # Кодируем промпт
    input_ids = encoder.encode(args.prompt)
    input_ids = torch.tensor([input_ids], dtype=torch.long, device=args.device)

    # Генерируем
    print(f"\nПромпт: {args.prompt}")
    print("-" * 60)

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids,
            args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )

    # Декодируем
    generated_text = encoder.decode(generated_ids[0].cpu().tolist())
    print(generated_text)
    print("-" * 60)


if __name__ == "__main__":
    main()