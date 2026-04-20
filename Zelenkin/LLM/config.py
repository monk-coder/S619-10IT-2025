import argparse


class Config:
    def __init__(self):
        self.vocab_size = 50257
        self.block_size = 128  # Уменьшили с 256
        self.n_layer = 4  # Уменьшили с 6
        self.n_head = 4  # Уменьшили с 6
        self.n_embd = 256  # Уменьшили с 384
        self.dropout = 0.1
        self.bias = True


def get_args():
    parser = argparse.ArgumentParser(description='Train GPT model')

    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--lr', type=float, default=6e-4, help='Learning rate')
    parser.add_argument('--max_iters', type=int, default=500, help='Maximum iterations')
    parser.add_argument('--eval_interval', type=int, default=100, help='Evaluation interval')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use')
    parser.add_argument('--gradient_clip', type=float, default=1.0, help='Gradient clipping norm')
    parser.add_argument('--warmup_iters', type=int, default=None, help='Warmup iterations')
    parser.add_argument('--eval_iters', type=int, default=50, help='Evaluation iterations')
    parser.add_argument('--save_interval', type=int, default=200, help='Checkpoint save interval')

    return parser.parse_args()