import argparse


def get_args():
    parser = argparse.ArgumentParser(description='Обучение GPT-подобной модели')

    # Данные
    parser.add_argument('--data_path', type=str, default='../0/data.txt',
                        help='Путь к файлу с данными')
    parser.add_argument('--vocab_size', type=int, default=5000,
                        help='Размер словаря')

    # Архитектура модели
    parser.add_argument('--embed_dim', type=int, default=384,
                        help='Размер эмбеддингов')
    parser.add_argument('--num_heads', type=int, default=6,
                        help='Количество голов внимания')
    parser.add_argument('--num_layers', type=int, default=6,
                        help='Количество слоев трансформера')
    parser.add_argument('--block_size', type=int, default=256,
                        help='Максимальная длина последовательности')

    # Обучение
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Размер батча')
    parser.add_argument('--lr', type=float, default=6e-4,
                        help='Начальная скорость обучения')
    parser.add_argument('--max_iters', type=int, default=5000,
                        help='Максимальное количество итераций')
    parser.add_argument('--eval_interval', type=int, default=500,
                        help='Интервал оценки на валидации')
    parser.add_argument('--eval_iters', type=int, default=200,
                        help='Количество итераций для оценки')
    parser.add_argument('--warmup_iters', type=int, default=500,
                        help='Количество итераций разогрева')
    parser.add_argument('--grad_clip', type=float, default=1.0,
                        help='Максимальная норма градиента')
    parser.add_argument('--weight_decay', type=float, default=0.1,
                        help='Коэффициент регуляризации')
    parser.add_argument('--device', type=str, default='cuda',
                        help='Устройство для обучения (cuda/cpu)')

    # Сохранение
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                        help='Директория для сохранения чекпоинтов')
    parser.add_argument('--save_interval', type=int, default=1000,
                        help='Интервал сохранения чекпоинтов')

    # Mixed precision
    parser.add_argument('--mixed_precision', action='store_true', default=True,
                        help='Использовать mixed precision')

    return parser.parse_args()