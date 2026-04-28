import torch
import argparse
from models.model import GPT, GPTConfig
from utils.data import BPETokenizer

def sample():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, default='checkpoints/best.pt')
    parser.add_argument('--tokenizer_path', type=str, default='../tokenizer.json')
    parser.add_argument('--prompt', type=str, default='ROMEO:')
    parser.add_argument('--max_new_tokens', type=int, default=200)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    ckpt = torch.load(args.checkpoint, map_location=device)
    config = GPTConfig(**ckpt['config'])
    
    model = GPT(config).to(device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    tokenizer = BPETokenizer(args.tokenizer_path)
    encoded_prompt = torch.tensor([tokenizer.encode(args.prompt)], dtype=torch.long, device=device)
    
    print(f" Prompt: {args.prompt}")
    generated = model.generate(encoded_prompt, args.max_new_tokens, args.temperature, args.top_k)
    print(f" Output:\n{tokenizer.decode(generated[0].tolist())}")

if __name__ == '__main__':
    sample()