# sample.py
import argparse
import torch
import os
from tokenizer import BPETokenizer
from model import TransformerLM
from config import parse_args as parse_train_args

def parse_args():
    parser = argparse.ArgumentParser(description='Generate text from trained model')
    parser.add_argument('--checkpoint', type=str, default='checkpoints/ckpt_best.pt', help='Path to model checkpoint')
    parser.add_argument('--prompt', type=str, default='Hello', help='Prompt for generation')
    parser.add_argument('--max_new_tokens', type=int, default=100, help='Max tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=20, help='Top-k filtering')
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu', help='Device')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load checkpoint
    if not os.path.exists(args.checkpoint):
        print(f"❌ Checkpoint not found: {args.checkpoint}")
        print("💡 Запустите сначала: python train.py")
        return
    
    print(f"📦 Loading checkpoint: {args.checkpoint}")
    ckpt = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    
    # Restore model and tokenizer
    model_args = ckpt['args']
    tokenizer = ckpt['tokenizer']
    
    model = TransformerLM(
        vocab_size=tokenizer.vocab_len,
        block_size=model_args.block_size,
        d_model=model_args.d_model,
        n_heads=model_args.n_heads,
        n_layers=model_args.n_layers,
        d_ff=model_args.d_ff,
        dropout=model_args.dropout
    )
    model.load_state_dict(ckpt['model'])
    model.to(args.device)
    model.eval()
    
    # Encode prompt
    prompt_ids = tokenizer.encode(args.prompt)
    if not prompt_ids:
        print("❌ Empty prompt encoding")
        return
    
    x = torch.tensor([prompt_ids], dtype=torch.long).to(args.device)
    
    # Generate
    print(f"🎲 Generating with temperature={args.temperature}, top_k={args.top_k}...")
    print(f"📝 Prompt: '{args.prompt}'")
    print("-" * 50)
    
    with torch.no_grad():
        y = model.generate(
            x, 
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )
    
    # Decode and print
    generated_text = tokenizer.decode(y[0].tolist())
    print(generated_text)
    print("-" * 50)
    print(f"✅ Generated {len(y[0]) - len(prompt_ids)} new tokens")

if __name__ == '__main__':
    main()