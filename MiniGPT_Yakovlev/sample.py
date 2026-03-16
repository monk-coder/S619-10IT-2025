import argparse
import numpy as np

import config
from tokenizer import BPETokenizer
from gpt import TransformerLM


def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    ids = tokenizer.encode(prompt)
    ids = ids[-model.max_seq_len:]
    eos_id = tokenizer.eos_token_id
    
    for _ in range(max_new_tokens):
        x = np.array([ids])
        logits = model.forward(x, training=False)[0, -1, :]
        
        if temperature != 1.0:
            logits = logits / temperature
        
        if top_k is not None:
            top_k = min(top_k, len(logits))
            top_idx = np.argsort(logits)[-top_k:]
            mask = np.ones_like(logits) * -1e9
            mask[top_idx] = 0
            logits = logits + mask
        
        probs = np.exp(logits - np.max(logits))
        probs = probs / probs.sum()
        next_id = np.random.choice(len(probs), p=probs)
        
        ids.append(int(next_id))
        if next_id == eos_id:
            break
    
    return tokenizer.decode(ids)


def sample(prompt, max_new_tokens=None, temperature=None, top_k=None, checkpoint=None):
    if max_new_tokens is None:
        max_new_tokens = config.MAX_NEW_TOKENS
    if temperature is None:
        temperature = config.TEMPERATURE
    if top_k is None:
        top_k = config.TOP_K
    if checkpoint is None:
        checkpoint = f"{config.SAVE_DIR}/model_weights.npz"
    
    print("Loading tokenizer...")
    tokenizer = BPETokenizer.load(config.TOKENIZER_PATH)
    config.VOCAB_SIZE = len(tokenizer)
    
    print("Initializing model...")
    model = TransformerLM(
        vocab_size=config.VOCAB_SIZE,
        d_model=config.D_MODEL,
        n_head=config.N_HEAD,
        n_layer=config.N_LAYER,
        d_ff=config.D_FF,
        max_seq_len=config.MAX_SEQ_LEN,
        dropout=0.0
    )
    
    print(f"Loading weights from {checkpoint}...")
    try:
        data = np.load(checkpoint, allow_pickle=True)
        params = {k: data[k] for k in data.files}
        model.load_params(params)
        print("Weights loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not load weights: {e}")
    
    print(f"\nPrompt: \"{prompt}\"")
    print("-" * 60)
    result = generate(model, tokenizer, prompt, max_new_tokens, temperature, top_k)
    print(result)
    print("-" * 60)
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="The future of")
    parser.add_argument('--max_new_tokens', type=int, default=None)
    parser.add_argument('--temperature', type=float, default=None)
    parser.add_argument('--top_k', type=int, default=None)
    parser.add_argument('--checkpoint', type=str, default=None)
    args = parser.parse_args()
    
    sample(
        args.prompt,
        args.max_new_tokens,
        args.temperature,
        args.top_k,
        args.checkpoint
    )
