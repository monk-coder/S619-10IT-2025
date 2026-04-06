import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from datasets import load_dataset
from tqdm import tqdm
import numpy as np
from collections import Counter

# ИСПОЛЬЗУЕМ ОТКРЫТУЮ МОДЕЛЬ - НЕ ТРЕБУЕТ ВХОДА!
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def normalize_answer(s):
    """Нормализация ответа для сравнения"""

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        return re.sub(r'[^\w\s]', '', text)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def compute_f1(prediction, ground_truth):
    """Вычисление F1 метрики"""
    pred_tokens = normalize_answer(prediction).split()
    truth_tokens = normalize_answer(ground_truth).split()

    if not pred_tokens or not truth_tokens:
        return int(pred_tokens == truth_tokens)

    common = Counter(pred_tokens) & Counter(truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0

    precision = num_same / len(pred_tokens)
    recall = num_same / len(truth_tokens)
    f1 = 2 * (precision * recall) / (precision + recall)

    return f1


def compute_em(prediction, ground_truth):
    """Вычисление Exact Match метрики"""
    return int(normalize_answer(prediction) == normalize_answer(ground_truth))


def evaluate_zero_shot(dataset, tokenizer, model, num_samples=100):
    """Zero-shot оценка"""
    print("Evaluating Zero-shot...")
    f1_scores = []
    em_scores = []

    for i, example in enumerate(tqdm(dataset.select(range(min(num_samples, len(dataset)))))):
        context = example["context"]
        question = example["question"]

        ground_truth = example["answers"]["text"][0] if example["answers"]["text"] else "No answer"

        prompt = f"Context: {context}\nQuestion: {question}\nAnswer: "

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "Answer:" in prediction:
            prediction = prediction.split("Answer:")[-1].strip()
        else:
            prediction = prediction.strip()

        f1 = compute_f1(prediction, ground_truth)
        em = compute_em(prediction, ground_truth)

        f1_scores.append(f1)
        em_scores.append(em)

    return np.mean(f1_scores), np.mean(em_scores)


def evaluate_few_shot(dataset, tokenizer, model, num_examples=5, num_samples=100):
    """Few-shot оценка с примерами"""
    print(f"Evaluating Few-shot with {num_examples} examples...")

    few_shot_examples = []
    for i in range(min(num_examples, len(dataset))):
        ex = dataset[i]
        if ex["answers"]["text"]:
            few_shot_examples.append({
                "context": ex["context"],
                "question": ex["question"],
                "answer": ex["answers"]["text"][0]
            })

    def format_few_shot_prompt(context, question, examples):
        prompt = ""
        for ex in examples:
            prompt += f"Context: {ex['context']}\nQuestion: {ex['question']}\nAnswer: {ex['answer']}\n\n"
        prompt += f"Context: {context}\nQuestion: {question}\nAnswer: "
        return prompt

    f1_scores = []
    em_scores = []

    test_start = num_examples
    test_end = min(test_start + num_samples, len(dataset))

    for i in tqdm(range(test_start, test_end)):
        example = dataset[i]
        context = example["context"]
        question = example["question"]
        ground_truth = example["answers"]["text"][0] if example["answers"]["text"] else "No answer"

        prompt = format_few_shot_prompt(context, question, few_shot_examples)

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "Answer:" in prediction:
            prediction = prediction.split("Answer:")[-1].strip()
        else:
            prediction = prediction.strip()

        f1 = compute_f1(prediction, ground_truth)
        em = compute_em(prediction, ground_truth)

        f1_scores.append(f1)
        em_scores.append(em)

    return np.mean(f1_scores), np.mean(em_scores)


def evaluate_finetuned(model_path, dataset, num_samples=100):
    """Оценка fine-tuned модели"""
    print("Evaluating Fine-tuned model...")

    # Загрузка fine-tuned модели на той же открытой модели
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,  # ← ИСПОЛЬЗУЕМ ОТКРЫТУЮ МОДЕЛЬ
        torch_dtype=torch.float16,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(base_model, model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token

    model.eval()

    f1_scores = []
    em_scores = []

    for i in tqdm(range(min(num_samples, len(dataset)))):
        example = dataset[i]
        context = example["context"]
        question = example["question"]
        ground_truth = example["answers"]["text"][0] if example["answers"]["text"] else "No answer"

        prompt = f"Context: {context}\nQuestion: {question}\nAnswer: "

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "Answer:" in prediction:
            prediction = prediction.split("Answer:")[-1].strip()
        else:
            prediction = prediction.strip()

        f1 = compute_f1(prediction, ground_truth)
        em = compute_em(prediction, ground_truth)

        f1_scores.append(f1)
        em_scores.append(em)

    return np.mean(f1_scores), np.mean(em_scores)


def main():
    print("Loading dataset...")
    squad = load_dataset("squad_v2")
    val_dataset = squad["validation"]

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60 + "\n")

    # Zero-shot evaluation
    print(f"Loading base model: {MODEL_NAME}")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    zero_shot_f1, zero_shot_em = evaluate_zero_shot(val_dataset, tokenizer, base_model, num_samples=50)
    print(f"Zero-shot Results:")
    print(f"  F1 Score: {zero_shot_f1:.3f}")
    print(f"  Exact Match: {zero_shot_em:.3f}\n")

    # Few-shot evaluation
    few_shot_f1, few_shot_em = evaluate_few_shot(val_dataset, tokenizer, base_model, num_examples=5, num_samples=50)
    print(f"Few-shot Results (5 examples):")
    print(f"  F1 Score: {few_shot_f1:.3f}")
    print(f"  Exact Match: {few_shot_em:.3f}\n")

    # Проверяем, есть ли fine-tuned модель
    import os
    if os.path.exists("./lora-squad-model"):
        finetuned_f1, finetuned_em = evaluate_finetuned("./lora-squad-model", val_dataset, num_samples=50)
        print(f"Fine-tuned (LoRA) Results:")
        print(f"  F1 Score: {finetuned_f1:.3f}")
        print(f"  Exact Match: {finetuned_em:.3f}\n")
    else:
        print("Fine-tuned model not found. Skipping...")
        finetuned_f1, finetuned_em = zero_shot_f1, zero_shot_em

    # Таблица результатов
    print("\n" + "=" * 60)
    print("FINAL RESULTS TABLE")
    print("=" * 60)
    print(f"{'Method':<20} {'F1 Score':<15} {'Exact Match':<15}")
    print("-" * 60)
    print(f"{'Zero-shot':<20} {zero_shot_f1:<15.3f} {zero_shot_em:<15.3f}")
    print(f"{'Few-shot (5 examples)':<20} {few_shot_f1:<15.3f} {few_shot_em:<15.3f}")
    if os.path.exists("./lora-squad-model"):
        print(f"{'LoRA Fine-tuned':<20} {finetuned_f1:<15.3f} {finetuned_em:<15.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()