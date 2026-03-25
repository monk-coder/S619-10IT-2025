# config.py
import argparse


def get_args():
    parser = argparse.ArgumentParser(description='Train Transformer Language Model')

    # Data
    parser.add_argument('--data_path', type=str, default='data.txt', help='Path to training data')
    parser.add_argument('--tokenizer_path', type=str, default='tokenizer.pkl', help='Path to BPE tokenizer')

    # Model architecture
    parser.add_argument('--d_model', type=int, default=256, help='Model dimension')
    parser.add_argument('--n_head', type=int, default=8, help='Number of attention heads')
    parser.add_argument('--n_layer', type=int, default=6, help='Number of transformer layers')
    parser.add_argument('--max_seq_len', type=int, default=512, help='Maximum sequence length')
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout rate')

    # Training
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size')
    parser.add_argument('--lr', type=float, default=6e-4, help='Learning rate')
    parser.add_argument('--max_iters', type=int, default=5000, help='Maximum training iterations')
    parser.add_argument('--warmup_iters', type=int, default=500, help='Warmup iterations')
    parser.add_argument('--eval_interval', type=int, default=500, help='Evaluation interval')
    parser.add_argument('--save_interval', type=int, default=1000, help='Checkpoint save interval')
    parser.add_argument('--grad_clip', type=float, default=1.0, help='Gradient clipping norm')
    parser.add_argument('--weight_decay', type=float, default=0.1, help='Weight decay')
    parser.add_argument('--beta1', type=float, default=0.9, help='Adam beta1')
    parser.add_argument('--beta2', type=float, default=0.95, help='Adam beta2')

    # System
    parser.add_argument('--device', type=str, default='cuda', choices=['cuda', 'cpu', 'mps'], help='Device to use')
    parser.add_argument('--dtype', type=str, default='float16', choices=['float16', 'bfloat16', 'float32'],
                        help='Mixed precision dtype')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--log_interval', type=int, default=10, help='Logging interval')

    # Checkpointing
    parser.add_argument('--resume', type=str, default=None, help='Resume from checkpoint')
    parser.add_argument('--output_dir', type=str, default='checkpoints', help='Output directory')

    return parser.parse_args()