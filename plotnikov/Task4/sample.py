import numpy as np
import argparse
from modules.transformer import TransformerLM
from utils.bpe_tokenizer import BPETokenizer

def load_model(path, model):
    data = np.load(path, allow_pickle=True)
    params = model.get_params()
    for param, grad, name in params:
        if name in data:
            param[:] = data[name]

def sample_top_k(logits, k, temperature=1.0):
    logits = logits / temperature
    if k > 0:
        top_k = np.sort(logits)[-k]
        logits = np.where(logits >= top_k, logits, -1e9)
    exp_logits = np.exp(logits - logits.max())
    probs = exp_logits / (exp_logits.sum() + 1e-8)
    return np.random.choice(len(probs), p=probs)

def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=50, block_size=128):
    context = tokenizer.encode(prompt)
    for _ in range(max_new_tokens):
        ctx = context[-block_size:]
        x = np.array([ctx], dtype=np.int32)
        logits = model.forward(x)
        next_logits = logits[0, -1, :]
        next_token = sample_top_k(next_logits, top_k, temperature)
        context.append(int(next_token))
    return tokenizer.decode(context)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='model.npz')
    parser.add_argument('--config', type=str, default='config.json')
    parser.add_argument('--data', type=str, default='data.txt')
    parser.add_argument('--prompt', type=str, default='the ')
    parser.add_argument('--max_tokens', type=int, default=100)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    args = parser.parse_args()
    
    import json
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    with open(args.data, 'r', encoding='utf-8') as f:
        text = f.read()
    
    tokenizer = BPETokenizer(config['vocab_size'])
    tokenizer.train(text)
    
    model = TransformerLM(
        vocab_size=tokenizer.vocab_len,
        d_model=config['d_model'],
        n_layer=config['n_layer'],
        n_head=config['n_head'],
        d_ff=config['d_ff'],
        max_len=config['block_size'],
        seed=config['seed']
    )
    
    load_model(args.model_path, model)
    
    print(f"🎲 Prompt: '{args.prompt}'")
    result = generate(model, tokenizer, args.prompt, args.max_tokens, args.temperature, args.top_k, config['block_size'])
    print(f" Generated:\n{result}")

if __name__ == '__main__':
    main()