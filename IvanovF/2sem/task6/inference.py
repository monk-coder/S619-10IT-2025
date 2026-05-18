"""
inference.py — локальный запуск с 3 демо-вопросами и интерактивным режимом.

Установка: pip install -r requirements.txt

Использование:
    python inference.py --adapter your-username/squad-llama-lora
    python inference.py --adapter ./lora-adapter --interactive
"""

import argparse
import torch
from unsloth import FastLanguageModel

DEMO_QUESTIONS = [
    {
        "context": (
            "The Amazon rainforest covers most of the Amazon basin of South America. "
            "This basin encompasses 7,000,000 km2, of which 5,500,000 km2 are covered by the rainforest."
        ),
        "question": "How large is the Amazon basin?",
        "gold": "7,000,000 km2",
    },
    {
        "context": (
            "Nikola Tesla was born on 10 July 1856 into a Serbian family in the village of "
            "Smiljan, in the Austrian Empire (modern-day Croatia)."
        ),
        "question": "Where was Nikola Tesla born?",
        "gold": "Smiljan",
    },
    {
        "context": (
            "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. "
            "It is named after the engineer Gustave Eiffel, whose company designed and built the tower."
        ),
        "question": "Who invented the telephone?",  # unanswerable
        "gold": "unanswerable",
    },
]


def make_prompt(context: str, question: str) -> str:
    return (
        f"### Context:\n{context}\n\n"
        f"### Question:\n{question}\n\n"
        f"### Answer:\n"
    )


def load_model(adapter_path: str):
    print(f"Загружаем модель: {adapter_path}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_path,
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    tokenizer.pad_token = tokenizer.eos_token
    print("✓ Модель загружена\n")
    return model, tokenizer


def generate_answer(model, tokenizer, context: str, question: str) -> str:
    device = next(model.parameters()).device
    prompt = make_prompt(context, question)
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


def run_demo(model, tokenizer):
    print("=" * 60)
    print("DEMO — 3 вопроса из SQuAD 2.0 val")
    print("=" * 60)
    for i, q in enumerate(DEMO_QUESTIONS, 1):
        pred = generate_answer(model, tokenizer, q["context"], q["question"])
        match = "✅" if pred.lower().strip() == q["gold"].lower().strip() else "⚠️"
        print(f"\n{match} [{i}] {q['question']}")
        print(f"   Контекст : {q['context'][:80]}...")
        print(f"   Эталон   : {q['gold']}")
        print(f"   Ответ    : {pred}")
    print()


def run_interactive(model, tokenizer):
    print("Интерактивный режим. Введите 'exit' для выхода.\n")
    while True:
        print("-" * 40)
        context = input("Context  : ").strip()
        if context.lower() == "exit":
            break
        question = input("Question : ").strip()
        if not context or not question:
            print("Нужно ввести и контекст, и вопрос.")
            continue
        answer = generate_answer(model, tokenizer, context, question)
        print(f"Answer   : {answer}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True, help="HF Hub repo или локальный путь к адаптеру")
    parser.add_argument("--interactive", action="store_true", help="Запустить интерактивный режим")
    args = parser.parse_args()

    model, tokenizer = load_model(args.adapter)
    run_demo(model, tokenizer)
    if args.interactive:
        run_interactive(model, tokenizer)


if __name__ == "__main__":
    main()