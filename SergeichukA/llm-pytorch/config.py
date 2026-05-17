# config.py
import argparse
import torch
import os

def get_default_device():
    return 'cuda' if torch.cuda.is_available() else 'cpu'

def get_default_dtype(device):
    if device == 'cuda' and torch.cuda.is_available():
        return torch.float16 if torch.cuda.is_bf16_supported() else torch.float16
    return torch.float32

def parse_args():
    parser = argparse.ArgumentParser(description='Mini GPT Training')
    
    # Data
    parser.add_argument('--data', type=str, default='data.txt', help='Path to training data')
    parser.add_argument('--tokenizer', type=str, default='tokenizer.pkl', help='Path to tokenizer')
    parser.add_argument('--vocab_size', type=int, default=500, help='Vocabulary size')
    parser.add_argument('--block_size', type=int, default=128, help='Max sequence length')
    
    # Model
    parser.add_argument('--d_model', type=int, default=128, help='Model dimension')
    parser.add_argument('--n_heads', type=int, default=4, help='Number of attention heads')
    parser.add_argument('--n_layers', type=int, default=2, help='Number of transformer blocks')
    parser.add_argument('--d_ff', type=int, default=512, help='FFN hidden dimension')
    parser.add_argument('--dropout', type=float, default=0.0, help='Dropout rate')
    
    # Training
    parser.add_argument('--max_iters', type=int, default=5000, help='Max training iterations')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-1, help='Weight decay')
    parser.add_argument('--grad_clip', type=float, default=1.0, help='Gradient clipping')
    parser.add_argument('--eval_interval', type=int, default=100, help='Evaluation interval')
    parser.add_argument('--eval_iters', type=int, default=10, help='Evaluation iterations')
    
    # Device & precision
    parser.add_argument('--device', type=str, default=get_default_device(), help='Device to train on')
    parser.add_argument('--dtype', type=str, default='float16' if torch.cuda.is_available() else 'float32', 
                       choices=['float32', 'float16', 'bfloat16'], help='Training precision')
    
    # Output
    parser.add_argument('--out_dir', type=str, default='checkpoints', help='Output directory')
    parser.add_argument('--seed', type=int, default=1337, help='Random seed')
    
    return parser.parse_args()

def setup_config(args):
    """Применяет настройки: device, dtype, seed, directories"""
    # Device
    if args.device == 'cuda' and not torch.cuda.is_available():
        print("⚠️ CUDA not available, falling back to CPU")
        args.device = 'cpu'
    
    # Dtype
    if args.dtype == 'float16' and args.device == 'cpu':
        print("⚠️ float16 not supported on CPU, using float32")
        args.dtype = 'float32'
    
    dtype_map = {'float32': torch.float32, 'float16': torch.float16, 'bfloat16': torch.bfloat16}
    args.torch_dtype = dtype_map[args.dtype]
    
    # Seed
    torch.manual_seed(args.seed)
    if args.device == 'cuda':
        torch.cuda.manual_seed(args.seed)
    
    # Directories
    os.makedirs(args.out_dir, exist_ok=True)
    
    return args