"""
evaluate.py — F1 / Exact Match для zero-shot, few-shot, LoRA.

Использование:
    python evaluate.py --adapter your-username/squad-llama-lora --mode all --n 500
"""

import argparse
import json
import re
import string
import collections
import numpy as np
import torch
from datasets import load_dataset
from tqdm import tqdm
from unsloth import FastLanguageModel


# ─── Метрики ──────────────────────────────────────────────────────

def normalize_answer(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    s = "".join(ch for ch in s if ch not in string.punctuation)
    return " ".join(s.split())

def token_f1(pred: str, gold: str) -> float:
    p = normalize_answer(pred).split()
    g = normalize_answer(gold).split()
    common = collections.Counter(p) & collections.Counter(g)
    nc = sum(common.values())
    if nc == 0:
        return 0.0
    return 2 * (nc / len(p)) * (nc / len(g)) / (nc / len(p) + nc / len(g))

def exact_match(pred: str, gold: str) -> float:
    return float(normalize_answer(pred) == normalize_answer(gold))

def best_over_golds(fn, pred, golds):
    if not golds:
        return fn(pred, "unanswerable")
    return max(fn(pred, g) for g in golds)


# ─── Промпты ──────────────────────────────────────────────────────

def make_prompt(context: str, question: str) -> str:
    return (
        f"### Context:\n{context}\n\n"
        f"### Question:\n{question}\n\n"
        f"### Answer:\n"
    )

def make_few_shot_prefix(few_shot_pool):
    def builder(ex):
        prefix = ""
        for s in few_shot_pool:
            if s["id"] == ex.get("id", ""):
                continue
            a = s["answers"]["text"]
            ans = a[0] if a else "unanswerable"
            prefix += (
                f"### Context:\n{s['context']}\n\n"
                f"### Question:\n{s['question']}\n\n"
                f"### Answer:\n{ans}\n\n"
            )
        return prefix
    return builder


# ─── Генерация ────────────────────────────────────────────────────

def generate_answer(model, tokenizer, context, question, prefix=""):
    device = next(model.parameters()).device
    prompt = prefix + make_prompt(context, question)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=48,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return generated.split("\n")[0].strip()


# ─── Цикл оценки ──────────────────────────────────────────────────

def evaluate(model, tokenizer, examples, prefix_fn=None, n=500):
    f1_scores, em_scores = [], []
    for ex in tqdm(examples[:n], desc="Evaluating"):
        prefix = prefix_fn(ex) if prefix_fn else ""
        pred = generate_answer(model, tokenizer, ex["context"], ex["question"], prefix)
        golds = ex["answers"]["text"]
        f1_scores.append(best_over_golds(token_f1,    pred, golds))
        em_scores.append(best_over_golds(exact_match, pred, golds))
    return {
        "f1": round(np.mean(f1_scores) * 100, 2),
        "em": round(np.mean(em_scores)  * 100, 2),
        "n":  min(n, len(examples)),
    }


# ─── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter",    required=True)
    parser.add_argument("--n",          type=int, default=500)
    parser.add_argument("--mode",       choices=["zero", "few", "lora", "all"], default="lora")
    parser.add_argument("--few_shot_n", type=int, default=5)
    parser.add_argument("--output",     default="eval_results.json")
    args = parser.parse_args()

    print("Загружаем SQuAD 2.0...")
    dataset  = load_dataset("squad_v2")
    val_list = list(dataset["validation"].shuffle(seed=42).select(range(args.n)))

    print(f"Загружаем модель: {args.adapter}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.adapter,
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    tokenizer.pad_token = tokenizer.eos_token

    results = {}

    if args.mode in ("zero", "all"):
        print("\n--- Zero-shot ---")
        results["zero_shot"] = evaluate(model, tokenizer, val_list, prefix_fn=None, n=args.n)
        r = results["zero_shot"]
        print(f"F1: {r['f1']}%  EM: {r['em']}%")

    if args.mode in ("few", "all"):
        print(f"\n--- Few-shot ({args.few_shot_n}) ---")
        pool = list(dataset["train"].select(range(args.few_shot_n)))
        results["few_shot"] = evaluate(model, tokenizer, val_list,
                                       prefix_fn=make_few_shot_prefix(pool), n=args.n)
        r = results["few_shot"]
        print(f"F1: {r['f1']}%  EM: {r['em']}%")

    if args.mode in ("lora", "all"):
        print("\n--- LoRA fine-tuned ---")
        results["lora"] = evaluate(model, tokenizer, val_list, prefix_fn=None, n=args.n)
        r = results["lora"]
        print(f"F1: {r['f1']}%  EM: {r['em']}%")

    print("\n" + "=" * 50)
    print(f"{'Метод':<22} {'F1':>8} {'EM':>8}")
    print("-" * 50)
    labels = {"zero_shot": "Zero-shot", "few_shot": f"Few-shot ({args.few_shot_n})", "lora": "LoRA"}
    for key, label in labels.items():
        if key in results:
            print(f"{label:<22} {results[key]['f1']:>7.1f}% {results[key]['em']:>7.1f}%")
    print("=" * 50)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Результаты сохранены: {args.output}")


if __name__ == "__main__":
    main()