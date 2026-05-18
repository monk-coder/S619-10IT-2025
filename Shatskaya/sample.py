import torch
import argparse
from model import MiniLLM
from config import Config

def generate(prompt, max_new_tokens=100, temperature=0.8, top_k=50):
    config = Config()
    model = MiniLLM(config).to(config.device)
    model.load_state_dict(torch.load("checkpoints/best_model.pt", map_location=config.device))
    model.eval()

    # Простая токенизация
    input_ids = torch.tensor([[ord(c) for c in prompt]], dtype=torch.long, device=config.device)
    
    for _ in range(max_new_tokens):
        logits = model(input_ids[:, -config.block_size:])
        logits = logits[:, -1, :] / temperature
        if top_k:
            v, _ = torch.topk(logits, top_k)
            logits[logits < v[:, [-1]]] = -float('Inf')
        probs = torch.nn.functional.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        input_ids = torch.cat([input_ids, next_token], dim=1)
    
    return ''.join([chr(x) for x in input_ids[0].tolist() if 32 <= x <= 126])

if name == "main":
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True)
    parser.add_argument('--temperature', type=float, default=0.8)
    args = parser.parse_args()
    print(generate(args.prompt, temperature=args.temperature))