import numpy as np
import json
import argparse
from model import GPT, softmax


def encode_text(text, vocab, merges, word_end):
    tokens = []
    words = text.split()
    for word in words:
        chars = list(word) + [word_end]
        tokens.extend(chars)
    for a, b in merges:
        new_token = a + b
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return [vocab.get(t, 0) for t in tokens]


def decode_ids(ids, inv_vocab):
    tokens = [inv_vocab.get(i, '<?>') for i in ids]
    text = ''.join(tokens)
    text = text.replace('</w>', ' ')
    return text.strip()


def generate(model, prompt_ids, max_new_tokens=20, temperature=0.8, top_k=5):
    idx = np.array(prompt_ids).reshape(1, -1)
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -model.seq_len:]
        logits = model.forward(idx_cond)

        next_logits = logits[:, -1, :] / temperature

        # Top-K filtering
        if top_k is not None:
            indices_to_remove = next_logits < np.sort(next_logits)[0, -top_k]
            next_logits[indices_to_remove] = -float('Inf')

        probs = softmax(next_logits, axis=-1)[0]
        next_idx = np.random.choice(len(probs), p=probs)
        idx = np.concatenate((idx, [[next_idx]]), axis=1)

    return idx[0].tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="мама")
    parser.add_argument('--tokens', type=int, default=15)
    parser.add_argument('--temp', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=5)
    args = parser.parse_args()

    with open('bpe_8000.json', 'r', encoding='utf-8') as f:
        bpe_data = json.load(f)

    vocab = bpe_data['vocab']
    merges = [tuple(m) for m in bpe_data['merges']]
    word_end = bpe_data['word_end']
    inv_vocab = {int(v): k for k, v in vocab.items()}

    model = GPT(
        vocab_size=len(vocab), d_model=128, n_head=4, n_layer=2, d_ff=256, seq_len=32
    )

    try:
        saved_params = np.load('model_weights.npy', allow_pickle=True)
        params, _ = model.get_params()
        for p, sp in zip(params, saved_params):
            if p.shape == sp.shape:
                p[:] = sp[:]
        print("Веса успешно загружены.")
    except Exception:
        print("Веса не найдены! Модель будет генерировать случайный текст.")

    ids = encode_text(args.prompt, vocab, merges, word_end)
    generated = generate(model, ids, max_new_tokens=args.tokens, temperature=args.temp, top_k=args.top_k)
    text = decode_ids(generated, inv_vocab)

    print("-" * 50)
    print(f"Промпт: {args.prompt}")
    print(f"Результат: {text}")
    print("-" * 50)


if __name__ == '__main__':
    main()