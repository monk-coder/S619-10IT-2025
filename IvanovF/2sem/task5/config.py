import argparse
import os


def get_config():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data", type=str, default="../task3/data.txt")
    parser.add_argument("--tokenizer", type=str, default="../task3/bpe_model.json")

    parser.add_argument("--d_model", type=int, default=256)
    parser.add_argument("--n_head", type=int, default=4)
    parser.add_argument("--n_layer", type=int, default=4)
    parser.add_argument("--T", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)

    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=6e-4)
    parser.add_argument("--max_iters", type=int, default=5000)
    parser.add_argument("--warmup_iters", type=int, default=None)
    parser.add_argument("--weight_decay", type=float, default=0.1)
    parser.add_argument("--max_norm", type=float, default=1.0)
    parser.add_argument("--beta1", type=float, default=0.9)
    parser.add_argument("--beta2", type=float, default=0.95)

    parser.add_argument("--eval_interval", type=int, default=500)
    parser.add_argument("--eval_iters", type=int, default=50)
    parser.add_argument("--save_interval", type=int, default=500)
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")

    parser.add_argument("--device", type=str, default="cuda" if _cuda_available() else "cpu")
    parser.add_argument("--amp", action="store_true", default=True)
    parser.add_argument("--compile", action="store_true", default=False)

    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    if args.warmup_iters is None:
        args.warmup_iters = args.max_iters // 10

    os.makedirs(args.checkpoint_dir, exist_ok=True)

    return args


def _cuda_available():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False