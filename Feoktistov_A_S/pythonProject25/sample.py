# sample.py
import torch
import pickle
import argparse
from model import TransformerLM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, required=True)
    parser.add_argument('--prompt', type=str, default='')
    parser.add_argument('--max_new_tokens', type=int, default=200)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()

    # Load checkpoint
    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    config = checkpoint['config']

    # Load tokenizer
    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    # Create model
    model = TransformerLM(
        vocab_size=tokenizer.vocab_size,
        d_model=config.d_model,
        n_head=config.n_head,
        n_layer=config.n_layer,
        max_seq_len=config.max_seq_len,
        dropout=0  # No dropout for inference
    )

    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(args.device)
    model.eval()

    # Tokenize prompt
    if args.prompt:
        prompt_tokens = tokenizer.encode(args.prompt)
        idx = torch.tensor([prompt_tokens], dtype=torch.long, device=args.device)
    else:
        idx = torch.tensor([[0]], dtype=torch.long, device=args.device)

    # Generate
    with torch.no_grad():
        generated = model.generate(
            idx,
            args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )

    # Decode
    generated_text = tokenizer.decode(generated[0].cpu().numpy())

    print("\n" + "=" * 60)
    print("GENERATED TEXT")
    print("=" * 60)
    print(generated_text)
    print("=" * 60)

    # Save to file
    with open('generated.txt', 'w', encoding='utf-8') as f:
        f.write(generated_text)


if __name__ == "__main__":
    main()