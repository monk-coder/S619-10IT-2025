import torch
import argparse
import os
from model import TransformerLM

def sample_top_k(logits, top_k=50, temperature=1.0):
    logits = logits[:, -1, :] / temperature
    if top_k is not None and top_k < logits.size(-1):
        v, _ = torch.topk(logits, top_k)
        logits[logits < v[:, [-1]]] = -float('inf')
    probs = torch.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1)

def generate(model, idx, max_new_tokens, temperature=1.0, top_k=None):
    for _ in range(max_new_tokens):
        if idx.size(1) >= model.block_size:
            idx = idx[:, -model.block_size:]
        logits = model(idx)
        idx_next = sample_top_k(logits, top_k=top_k, temperature=temperature)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, default='checkpoints/ckpt_best.pt')
    parser.add_argument('--prompt', type=str, default='ROMEO:')
    parser.add_argument('--max_new_tokens', type=int, default=200)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    parser.add_argument('--seed', type=int, default=1337)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    ckpt = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    tokenizer = ckpt['tokenizer']
    cfg = ckpt['config']
    
    model = TransformerLM(tokenizer.vocab_len, cfg.block_size, d_model=128, n_heads=4, n_layers=2, d_ff=512)
    model.load_state_dict(ckpt['model'])
    model.eval()

    context = tokenizer.encode(args.prompt)
    if len(context) == 0: context = [getattr(tokenizer, 'unk_id', 0)]
    x = torch.tensor([context], dtype=torch.long)

    print(f"📝 Prompt: {args.prompt}")
    y = generate(model, x, args.max_new_tokens, args.temperature, args.top_k)
    print(f"🤖 Generated:\n{tokenizer.decode(y[0].tolist())}\n")

if __name__ == '__main__':
    main()