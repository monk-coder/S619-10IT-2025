#!/usr/bin/env python3
import argparse
import numpy as np
from transformer import TransformerLM
from data import load_tokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ckpt', type=str, required=True, help='Path to .npz checkpoint')
    parser.add_argument('--prompt', type=str, default='once upon')
    parser.add_argument('--max_tokens', type=int, default=100)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    parser.add_argument('--seq_len', type=int, default=128)
    parser.add_argument('--d_model', type=int, default=128)
    parser.add_argument('--n_layer', type=int, default=2)
    parser.add_argument('--n_head', type=int, default=2)
    parser.add_argument('--d_ff', type=int, default=256)
    parser.add_argument('--tokenizer_path', type=str, default='tokenizer.json')
    args = parser.parse_args()
    
    tokenizer = load_tokenizer(args.tokenizer_path)
    
    model = TransformerLM(
        vocab_size=len(tokenizer),
        max_seq_len=args.seq_len,
        d_model=args.d_model,
        n_layer=args.n_layer,
        n_head=args.n_head,
        d_ff=args.d_ff,
        dropout=0.0
    )
    
    print(f"Loading checkpoint: {args.ckpt}")
    ckpt = np.load(args.ckpt)
    model.load_params({k: ckpt[k] for k in ckpt.files})
    
    prompt_ids = tokenizer.encode(args.prompt)
    print(f"\nPrompt: {args.prompt}")
    print(f"Prompt tokens: {prompt_ids}")
    out_ids = model.generate(prompt_ids, args.max_tokens, args.temperature, args.top_k)
    print(f"Output: {tokenizer.decode(out_ids)}\n")


if __name__ == '__main__':
    main()