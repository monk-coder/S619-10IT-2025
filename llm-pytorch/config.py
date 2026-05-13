"""
Конфигурация модели и аргументы командной строки
"""

import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Train GPT model')
    
    # Данные
    parser.add_argument('--data_path', type=str, default='data.txt',
                        help='Path to training data')
    parser.add_argument('--block_size', type=int, default=256,
                        help='Context length for training')
    
    # Модель
    parser.add_argument('--vocab_size', type=int, default=10000,
                        help='Vocabulary size (for BPE)')
    parser.add_argument('--n_embd', type=int, default=384,
                        help='Embedding dimension')
    parser.add_argument('--n_head', type=int, default=6,
                        help='Number of attention heads')
    parser.add_argument('--n_layer', type=int, default=6,
                        help='Number of transformer layers')
    parser.add_argument('--dropout', type=float, default=0.2,
                        help='Dropout rate')
    
    # Обучение
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Batch size for training')
    parser.add_argument('--max_iters', type=int, default=5000,
                        help='Maximum training iterations')
    parser.add_argument('--lr', type=float, default=6e-4,
                        help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=0.01,
                        help='Weight decay')
    parser.add_argument('--warmup_iters', type=int, default=500,
                        help='Number of warmup iterations')
    parser.add_argument('--eval_interval', type=int, default=500,
                        help='Evaluate every N steps')
    parser.add_argument('--eval_iters', type=int, default=200,
                        help='Number of iterations for evaluation')
    parser.add_argument('--grad_clip', type=float, default=1.0,
                        help='Gradient clipping norm')
    parser.add_argument('--device', type=str, default='cuda',
                        choices=['cuda', 'cpu', 'mps'],
                        help='Device to train on')
    parser.add_argument('--dtype', type=str, default='float16',
                        help='Mixed precision dtype')
    
    # Сэмплирование
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='Path to checkpoint for sampling')
    parser.add_argument('--prompt', type=str, default="ROMEO:",
                        help='Prompt for generation')
    parser.add_argument('--max_new_tokens', type=int, default=200,
                        help='Number of tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=50,
                        help='Top-k sampling parameter')
    
    # Система
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--log_interval', type=int, default=100,
                        help='Log every N steps')
    parser.add_argument('--save_interval', type=int, default=1000,
                        help='Save checkpoint every N steps')
    
    return parser.parse_args()