import numpy as np
import argparse
import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))
from model import TransformerLM, softmax
from bpe_tokenizer import BPETokenizer


def generate(model, tokenizer, prompt, max_new_tokens=50, temperature=1.0, top_k=None):
    ids = list(tokenizer.encode(prompt))
    T = model.T
    prompt_len = len(ids)

    for _ in range(max_new_tokens):
        context = ids[-T:]
        seq_len = len(context)

        x = np.array(context, dtype=np.int32)[None, :]

        if seq_len < T:
            # паддим справа чтобы размер был T, но берём логит последнего реального токена
            pad = np.zeros((1, T - seq_len), dtype=np.int32)
            x_padded = np.concatenate([x, pad], axis=1)
            logits = model.forward(x_padded)
            logit_last = logits[0, seq_len - 1]
        else:
            logits = model.forward(x)
            logit_last = logits[0, T - 1]

        logit_last = logit_last / max(temperature, 1e-9)

        if top_k is not None and top_k > 0:
            top_indices = np.argsort(logit_last)[::-1][:top_k]
            mask = np.full(len(logit_last), -1e9, dtype=np.float32)
            mask[top_indices] = logit_last[top_indices]
            logit_last = mask

        probs = softmax(logit_last)
        next_id = int(np.random.choice(len(probs), p=probs))
        ids.append(next_id)

    return tokenizer.decode(ids[prompt_len:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt_model")
    parser.add_argument("--tokenizer", type=str, default="../task3/bpe_model.json")
    parser.add_argument("--prompt", type=str, default="the quick")
    parser.add_argument("--max_new_tokens", type=int, default=50)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    np.random.seed(args.seed)

    cfg_path = args.model + "_config.json"
    if not os.path.exists(cfg_path):
        print(f"конфиг не найден: {cfg_path}")
        sys.exit(1)

    with open(cfg_path) as f:
        cfg = json.load(f)

    tokenizer = BPETokenizer.load(args.tokenizer)

    model = TransformerLM(
        vocab_size=cfg["vocab_size"],
        d_model=cfg["d_model"],
        n_head=cfg["n_head"],
        n_layer=cfg["n_layer"],
        T=cfg["T"],
    )
    model = TransformerLM.load(args.model)

    print(f"prompt: {repr(args.prompt)}")
    result = generate(
        model, tokenizer, args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
    )
    print(f"generated: {repr(result)}")
    print()
    print(args.prompt + result)


if __name__ == "__main__":
    main()