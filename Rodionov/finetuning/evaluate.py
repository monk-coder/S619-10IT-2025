import evaluate
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from datasets import load_dataset
from tqdm import tqdm
import re
import string
from collections import Counter


class SQuADEvaluator:
    def __init__(self, model_path, device="cuda"):
        self.device = device
        base_model_name = "meta-llama/Llama-3.2-1B"

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto"
        )

        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.eval()

        self.squad_metric = evaluate.load("squad_v2")

    def normalize_answer(self, s):
        """Нормализация ответа для сравнения"""

        def remove_articles(text):
            return re.sub(r'\b(a|an|the)\b', ' ', text)

        def white_space_fix(text):
            return ' '.join(text.split())

        def remove_punc(text):
            exclude = set(string.punctuation)
            return ''.join(ch for ch in text if ch not in exclude)

        def lower(text):
            return text.lower()

        return white_space_fix(remove_articles(remove_punc(lower(s))))

    def compute_f1(self, prediction, ground_truths):
        """Вычисление F1 score"""
        prediction_tokens = self.normalize_answer(prediction).split()

        best_f1 = 0
        for truth in ground_truths:
            truth_tokens = self.normalize_answer(truth).split()

            if len(prediction_tokens) == 0 or len(truth_tokens) == 0:
                return int(prediction_tokens == truth_tokens)

            common = Counter(prediction_tokens) & Counter(truth_tokens)
            num_same = sum(common.values())

            if num_same == 0:
                continue

            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(truth_tokens)
            f1 = (2 * precision * recall) / (precision + recall)

            best_f1 = max(best_f1, f1)

        return best_f1

    def compute_exact_match(self, prediction, ground_truths):
        """Вычисление Exact Match"""
        normalized_prediction = self.normalize_answer(prediction)

        for truth in ground_truths:
            if normalized_prediction == self.normalize_answer(truth):
                return 1.0

        return 0.0

    def predict_answer(self, context, question):
        """Генерация ответа моделью"""
        prompt = f"""Context: {context}

Question: {question}

Answer:"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = generated_text.split("Answer:")[-1].strip()

        # Удаляем лишние переносы строк
        answer = answer.split('\n')[0].strip()

        return answer if answer else "No answer"

    def evaluate_zero_shot(self, num_samples=100):
        """Zero-shot оценка базовой модели"""
        print("Running zero-shot evaluation...")

        base_model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto"
        )
        base_model.eval()

        squad = load_dataset("squad_v2", split="validation")
        squad_sample = squad.select(range(num_samples))

        f1_scores = []
        em_scores = []

        for example in tqdm(squad_sample):
            prompt = f"""Context: {example['context']}

Question: {example['question']}

Answer:"""

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = base_model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            prediction = generated_text.split("Answer:")[-1].strip().split('\n')[0]

            ground_truths = example['answers']['text'] if example['answers']['text'] else [""]

            f1 = self.compute_f1(prediction, ground_truths)
            em = self.compute_exact_match(prediction, ground_truths)

            f1_scores.append(f1)
            em_scores.append(em)

        return {
            "f1": sum(f1_scores) / len(f1_scores) * 100,
            "exact_match": sum(em_scores) / len(em_scores) * 100
        }

    def evaluate_fine_tuned(self, num_samples=1000):
        """Оценка fine-tuned модели"""
        print("Running fine-tuned evaluation...")

        squad = load_dataset("squad_v2", split="validation")
        squad_sample = squad.select(range(min(num_samples, len(squad))))

        f1_scores = []
        em_scores = []

        for example in tqdm(squad_sample):
            prediction = self.predict_answer(example['context'], example['question'])
            ground_truths = example['answers']['text'] if example['answers']['text'] else [""]

            f1 = self.compute_f1(prediction, ground_truths)
            em = self.compute_exact_match(prediction, ground_truths)

            f1_scores.append(f1)
            em_scores.append(em)

        return {
            "f1": sum(f1_scores) / len(f1_scores) * 100,
            "exact_match": sum(em_scores) / len(em_scores) * 100
        }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="your-username/squad-llama-lora")
    parser.add_argument("--num_samples", type=int, default=100)
    parser.add_argument("--eval_type", choices=["zero_shot", "fine_tuned", "both"], default="both")
    args = parser.parse_args()

    evaluator = SQuADEvaluator(args.model_path)

    results = {}

    if args.eval_type in ["zero_shot", "both"]:
        zero_shot_results = evaluator.evaluate_zero_shot(args.num_samples)
        results["Zero-shot"] = zero_shot_results
        print(f"\nZero-shot Results:")
        print(f"F1: {zero_shot_results['f1']:.2f}%")
        print(f"Exact Match: {zero_shot_results['exact_match']:.2f}%")

    if args.eval_type in ["fine_tuned", "both"]:
        fine_tuned_results = evaluator.evaluate_fine_tuned(args.num_samples * 10)
        results["Fine-tuned (LoRA)"] = fine_tuned_results
        print(f"\nFine-tuned Results:")
        print(f"F1: {fine_tuned_results['f1']:.2f}%")
        print(f"Exact Match: {fine_tuned_results['exact_match']:.2f}%")

    # Сохраняем результаты
    import json
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 50)
    print("Summary Table:")
    print("-" * 50)
    print(f"{'Method':<20} {'F1':<15} {'Exact Match':<15}")
    print("-" * 50)
    for method, scores in results.items():
        print(f"{method:<20} {scores['f1']:.2f}%{'':<8} {scores['exact_match']:.2f}%")


if __name__ == "__main__":
    main()