"""
Генерация текста с помощью обученной GPT модели.
"""

import argparse
import json
import torch
import numpy as np
from model import GPT


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


def load_bpe(path='bpe_8000.json'):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    vocab = data['vocab']
    merges = [tuple(m) for m in data['merges']]
    word_end = data['word_end']
    inv_vocab = {int(v): k for k, v in vocab.items()}
    return vocab, merges, word_end, inv_vocab


def create_causal_mask(seq_len, device):
    return torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()


def generate(model, prompt_ids, max_new_tokens=50, temperature=0.8, top_k=50, device='cpu'):
    model.eval()
    idx = torch.tensor(prompt_ids, device=device).unsqueeze(0)

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -model.seq_len:]
        mask = create_causal_mask(idx_cond.shape[1], device)

        with torch.no_grad():
            logits = model(idx_cond, mask)

        logits = logits[0, -1, :] / (temperature + 1e-8)  # защита от деления на 0

        if top_k is not None and top_k > 0:
            top_logits, top_indices = torch.topk(logits, min(top_k, logits.size(-1)))
            logits = torch.full_like(logits, float('-inf'))
            logits[top_indices] = top_logits

        probs = torch.softmax(logits, dim=-1)
        next_idx = torch.multinomial(probs, 1)
        idx = torch.cat((idx, next_idx.unsqueeze(0)), dim=1)

    return idx[0].tolist()


def main():
    parser = argparse.ArgumentParser(description='Генерация текста с помощью GPT')
    parser.add_argument('--checkpoint', type=str, default='checkpoints/best_model.pt', help='Путь к модели')
    parser.add_argument('--bpe_path', type=str, default='bpe_8000.json', help='Путь к BPE')
    parser.add_argument('--prompt', type=str, default='мама', help='Начальный промпт')
    parser.add_argument('--tokens', type=int, default=50, help='Количество генерируемых токенов')
    parser.add_argument('--temperature', type=float, default=0.8, help='Температура')
    parser.add_argument('--top_k', type=int, default=50, help='Top-K фильтрация')
    parser.add_argument('--seq_len', type=int, default=128, help='Длина контекста')
    parser.add_argument('--d_model', type=int, default=256)
    parser.add_argument('--n_head', type=int, default=8)
    parser.add_argument('--n_layer', type=int, default=3)
    parser.add_argument('--d_ff', type=int, default=512)
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')

    args = parser.parse_args()

    device = torch.device(args.device)
    print(f"Используется устройство: {device}")

    vocab, merges, word_end, inv_vocab = load_bpe(args.bpe_path)
    vocab_size = len(vocab)

    model = GPT(
        vocab_size=vocab_size,
        d_model=args.d_model,
        n_head=args.n_head,
        n_layer=args.n_layer,
        d_ff=args.d_ff,
        seq_len=args.seq_len
    ).to(device)

    try:
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))
        print(f"✅ Модель загружена из {args.checkpoint}")
    except FileNotFoundError:
        print(f"⚠️ Файл {args.checkpoint} не найден, используется случайная инициализация")

    prompt_ids = encode_text(args.prompt, vocab, merges, word_end)
    print(f"Промпт: {args.prompt}")

    generated_ids = generate(
        model, prompt_ids,
        max_new_tokens=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=device
    )

    generated_text = decode_ids(generated_ids, inv_vocab)
    print(f"\nРезультат:\n{generated_text}")


if __name__ == '__main__':
    main()