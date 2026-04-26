import os
import sys
import argparse
import torch

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))

from model import TransformerLM
from bpe_tokenizer import BPETokenizer


def load_model(checkpoint_path, device):
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    model = TransformerLM(
        vocab_size=cfg["vocab_size"],
        d_model=cfg["d_model"],
        n_head=cfg["n_head"],
        n_layer=cfg["n_layer"],
        T=cfg["T"],
        dropout=0.0,
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best.pt")
    parser.add_argument("--tokenizer", type=str, default="../task3/bpe_model.json")
    parser.add_argument("--prompt", type=str, default="Князь")
    parser.add_argument("--max_new_tokens", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    tok = BPETokenizer.load(args.tokenizer)
    model = load_model(args.checkpoint, args.device)

    print(f"checkpoint: {args.checkpoint}")
    print(f"prompt: {repr(args.prompt)}")
    print("-" * 50)

    ids = tok.encode(args.prompt)
    x = torch.tensor([ids], dtype=torch.long, device=args.device)

    out = model.generate(x, args.max_new_tokens, temperature=args.temperature, top_k=args.top_k)
    generated_ids = out[0, len(ids):].tolist()
    print(args.prompt + tok.decode(generated_ids))


if __name__ == "__main__":
    main()