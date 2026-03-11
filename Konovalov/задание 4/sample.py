import numpy as np
import pickle
import argparse

from tokenizer import BPETokenizer
from model import TransformerLM

def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    context = tokenizer.encode(prompt)
    context = np.array(context).reshape(1, -1)
    for _ in range(max_new_tokens):
        if context.shape[1] > model.pos_encoding.params['pe'].shape[0]:
            context = context[:, -model.pos_encoding.params['pe'].shape[0]:]
        logits = model.forward(context)
        logits = logits[0, -1, :]

        logits = logits / temperature

        if top_k is not None:
            indices = np.argpartition(logits, -top_k)[-top_k:]
            mask = np.ones_like(logits) * -np.inf
            mask[indices] = logits[indices]
            logits = mask

        probs = np.exp(logits - np.max(logits))
        probs = probs / np.sum(probs)

        next_token = np.random.choice(len(probs), p=probs)
        context = np.concatenate([context, np.array([[next_token]])], axis=1)

    return tokenizer.decode(context[0].tolist())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default='Привет')
    parser.add_argument('--max_new_tokens', type=int, default=50)
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--top_k', type=int, default=None)
    args = parser.parse_args()

    with open('../tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    with open('model_params.pkl', 'rb') as f:
        saved_params = pickle.load(f)

    vocab_size = 500
    d_model = 128
    n_layer = 2
    n_head = 2
    max_len = 256

    model = TransformerLM(vocab_size, d_model, n_layer, n_head, max_len)

    model_params, _ = model.parameters()
    for k in saved_params:
        if k in model_params:
            model_params[k][:] = saved_params[k]

    output = generate(model, tokenizer, args.prompt, args.max_new_tokens,
                      args.temperature, args.top_k)
    print(output)

if __name__ == '__main__':
    main()
