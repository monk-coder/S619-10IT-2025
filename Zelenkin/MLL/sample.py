import numpy as np
import argparse
import pickle
from core import TransformerLM
from bpe_tokenizer import BPETokenizer  # Используем BPETokenizer


def generate_text(model, tokenizer, prompt, max_new_tokens=100, temperature=0.7):
    """Generate text with temperature sampling"""
    print(f"Generating with prompt: '{prompt}'")
    tokens = tokenizer.encode(prompt)
    print(f"Initial tokens: {len(tokens)}")

    for step in range(max_new_tokens):
        # Get context
        context = tokens[-model.max_seq_len:]
        x = np.array([context])

        # Forward pass
        logits = model.forward(x)

        # Get logits for last token
        next_logits = logits[0, -1, :] / temperature

        # Softmax
        exp_logits = np.exp(next_logits - np.max(next_logits))
        probs = exp_logits / (np.sum(exp_logits) + 1e-8)

        # Sample next token
        next_token = np.random.choice(len(probs), p=probs)
        tokens.append(next_token)

        # Optional: show progress
        if step % 20 == 0 and step > 0:
            partial = tokenizer.decode(tokens)
            print(f"Step {step}: {partial[:50]}...")

    return tokenizer.decode(tokens)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="The", help='Prompt text')
    parser.add_argument('--max_tokens', type=int, default=100, help='Maximum new tokens')
    parser.add_argument('--temperature', type=float, default=0.7, help='Sampling temperature')
    args = parser.parse_args()

    # Load tokenizer from file
    try:
        with open('tokenizer.pkl', 'rb') as f:
            tokenizer = pickle.load(f)
        print("Tokenizer loaded from tokenizer.pkl")
    except FileNotFoundError:
        print("tokenizer.pkl not found, creating new tokenizer from data.txt")
        tokenizer = BPETokenizer()
        with open('data.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        tokenizer.train(text, vocab_size=300)
        with open('tokenizer.pkl', 'wb') as f:
            pickle.dump(tokenizer, f)
        print("Tokenizer saved to tokenizer.pkl")

    # Load model
    try:
        model_data = np.load('model_final.npy', allow_pickle=True).item()
        vocab_size = len(tokenizer.vocab)  # Use actual vocab size from tokenizer
        d_model = model_data.get('d_model', 64)
        n_layer = model_data.get('n_layer', 2)
        n_head = model_data.get('n_head', 2)
        max_seq_len = model_data.get('max_seq_len', 32)

        print(f"Loading model with: d_model={d_model}, n_layer={n_layer}, n_head={n_head}")
        model = TransformerLM(vocab_size, d_model, n_layer, n_head, max_seq_len)
        model.token_embedding = model_data['token_embedding']
        model.pos_embedding = model_data['pos_embedding']
        print("Loaded trained model!")
    except Exception as e:
        print(f"Could not load trained model: {e}")
        print("Using random model")
        vocab_size = len(tokenizer.vocab)
        model = TransformerLM(vocab_size, 64, 2, 2, 32)

    print(f"Vocabulary size: {vocab_size}")
    print(f"Model max sequence length: {model.max_seq_len}")
    print(f"Temperature: {args.temperature}")

    # Generate
    print("\n" + "=" * 60)
    print(f"PROMPT: '{args.prompt}'")
    print("-" * 60)

    generated = generate_text(model, tokenizer, args.prompt, args.max_tokens, args.temperature)

    print(f"\nGENERATED TEXT:\n{generated}")
    print("=" * 60)


if __name__ == "__main__":
    main()