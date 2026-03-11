import numpy as np
import json
import argparse
from tokenizer import BPETokenizer
from model import TransformerLM

def load_model(path="model_weights.json", config=None):
    with open(path, 'r') as f:
        weights = json.load(f)
    params = {k: np.array(v) for k, v in weights.items()}
    
    if config is None:
        config = {
            "vocab_size": 512,
            "d_model": 128,
            "n_head": 4,
            "n_layer": 2,
            "max_seq_len": 128,
            "d_ff": 512
        }
    
    model = TransformerLM(
        vocab_size=config["vocab_size"],
        d_model=config["d_model"],
        n_head=config["n_head"],
        n_layer=config["n_layer"],
        max_seq_len=config["max_seq_len"],
        d_ff=config["d_ff"]
    )
    
    for k, v in params.items():
        if k in model.params:
            model.params[k] = v
            
    return model

def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    model.zero_grad()
    
    input_ids = tokenizer.encode(prompt)
    if len(input_ids) > 128:
        input_ids = input_ids[-128:]
        
    context = np.array(input_ids).reshape(1, -1)
    generated = list(context[0])
    
    print(f"\nPrompt: {prompt}")
    print("Generating...", end="", flush=True)
    
    for i in range(max_new_tokens):
        if context.shape[1] > 128:
            context = context[:, -128:]
            
        logits = model.forward(context)
        last_logits = logits[0, -1, :] / temperature
        
        if top_k is not None:
            indices_to_remove = last_logits < np.sort(last_logits)[-top_k]
            last_logits[indices_to_remove] = -1e9
            
        exp_logits = np.exp(last_logits - np.max(last_logits))
        probs = exp_logits / np.sum(exp_logits)
        
        next_id = np.random.choice(len(probs), p=probs)
        
        # Stop if EOS or PAD
        if next_id >= len(tokenizer.id_to_token):
            break
        token_str = tokenizer.id_to_token.get(next_id, "")
        if token_str in ["<pad>", "<eos>"]:
            break
            
        generated.append(next_id)
        context = np.array(generated).reshape(1, -1)
        print(".", end="", flush=True)
        
    print("\n")
    return tokenizer.decode(generated)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, default="The quick")
    parser.add_argument("--max_tokens", type=int, default=50)
    parser.add_argument("--temperature", type=float, default=0.8)
    args = parser.parse_args()
    
    tokenizer = BPETokenizer()
    try:
        tokenizer.load("tokenizer.json")
    except FileNotFoundError:
        print("Tokenizer not found. Run train.py first.")
        exit(1)
        
    config = {
        "vocab_size": tokenizer.vocab_size,
        "d_model": 128,
        "n_head": 4,
        "n_layer": 2,
        "max_seq_len": 128,
        "d_ff": 512
    }
    try:
        model = load_model(config=config)
    except FileNotFoundError:
        print("Model weights not found. Run train.py first.")
        exit(1)
        
    text = generate(model, tokenizer, args.prompt, args.max_tokens, args.temperature, top_k=40)
    print(f"Generated:\n{text}")