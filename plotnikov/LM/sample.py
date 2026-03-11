import numpy as np
import argparse
import json
from bpe_tokenizer import BPETokenizer
from transformer_lm import TransformerLM
from utils import sample_next_token
from constants import N_LAYERS, N_HEADS, D_MODEL, D_FF, MAX_SEQ_LEN


def load_model(model_path: str, tokenizer: BPETokenizer) -> TransformerLM:
    vocab_size = tokenizer.get_vocab_size()
    model = TransformerLM(vocab_size, N_LAYERS, N_HEADS, D_MODEL, D_FF, MAX_SEQ_LEN)
    
    data = np.load(model_path)
    model.token_embedding = data['token_embedding']
    model.pos_embedding = data['pos_embedding']
    model.output_proj = data['output_proj']
    model.ln_final.gamma = data['ln_final_gamma']
    model.ln_final.beta = data['ln_final_beta']
    
    return model


def generate(model: TransformerLM, tokenizer: BPETokenizer, prompt: str, max_new_tokens: int = 50, temperature: float = 0.7, top_k: int = 40) -> str:
    tokens = tokenizer.encode(prompt)
    tokens = tokens[:MAX_SEQ_LEN]
    
    for _ in range(max_new_tokens):
        if len(tokens) > MAX_SEQ_LEN:
            input_tokens = tokens[-MAX_SEQ_LEN:]
        else:
            input_tokens = tokens
        
        x = np.array([input_tokens], dtype=np.int32)
        logits = model.forward(x, training=False)
        
        next_token_logits = logits[0, -1, :]
        next_token_id = sample_next_token(next_token_logits, temperature=temperature, top_k=top_k)
        
        tokens.append(next_token_id)
        
        if next_token_id == tokenizer.special_tokens["<EOS>"]:
            break
    
    return tokenizer.decode(tokens)


def main():
    parser = argparse.ArgumentParser(description='Generate text with trained Transformer LM')
    parser.add_argument('--prompt', type=str, default="The quick brown fox", help='Prompt text for generation')
    parser.add_argument('--max_new_tokens', type=int, default=50, help='Maximum number of tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.7, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=40, help='Top-k sampling parameter')
    parser.add_argument('--model_path', type=str, default='model_weights.npz', help='Path to model weights')
    parser.add_argument('--tokenizer_path', type=str, default='tokenizer.json', help='Path to tokenizer')
    
    args = parser.parse_args()
    
    print("Loading tokenizer...")
    tokenizer = BPETokenizer()
    tokenizer.load(args.tokenizer_path)
    
    print("Loading model...")
    model = load_model(args.model_path, tokenizer)
    
    print(f"\nPrompt: '{args.prompt}'")
    print("-" * 60)
    
    generated = generate(
        model=model,
        tokenizer=tokenizer,
        prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k
    )
    
    print(generated)
    print("-" * 60)
    
    print("\nAdditional examples:")
    examples = [
        "Machine learning",
        "Artificial intelligence is",
        "In the beginning"
    ]
    
    for example in examples:
        print(f"\nPrompt: '{example}'")
        print("-" * 60)
        result = generate(model, tokenizer, example, max_new_tokens=40, temperature=0.8, top_k=30)
        print(result)
        print("-" * 60)


if __name__ == "__main__":
    main()