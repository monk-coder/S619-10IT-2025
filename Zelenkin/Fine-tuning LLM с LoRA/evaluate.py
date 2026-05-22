import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from peft import PeftModel
import re


# Заметь: используем стандартные коллекции list, dict. Никакого typing!
def normalize_answer(s: str) -> str:
    """Удаляет артикли, пунктуацию и приводит к нижнему регистру для честного сравнения."""

    def remove_articles(text: str) -> str:
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text: str) -> str:
        return ' '.join(text.split())

    def remove_punc(text: str) -> str:
        exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text: str) -> str:
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def exact_match_score(prediction: str, ground_truth: str) -> float:
    return int(normalize_answer(prediction) == normalize_answer(ground_truth))


def f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    truth_tokens = normalize_answer(ground_truth).split()

    if len(pred_tokens) == 0 or len(truth_tokens) == 0:
        return int(pred_tokens == truth_tokens)

    common_tokens = set(pred_tokens) & set(truth_tokens)
    if len(common_tokens) == 0:
        return 0.0

    prec = len(common_tokens) / len(pred_tokens)
    rec = len(common_tokens) / len(truth_tokens)
    return 2 * (prec * rec) / (prec + rec)


def evaluate_model(model, tokenizer, dataset, strategy: str, device: str, few_shot_examples: str = "") -> dict[
    str, float]:
    f1_total = 0.0
    em_total = 0.0
    count = 0

    print(f"\n--- Запуск оценки: {strategy} ---")
    for item in dataset:
        context = item['context']
        question = item['question']
        answers = item['answers']['text']
        true_answer = answers[0] if len(answers) > 0 else "Unanswerable"

        prompt = f"{few_shot_examples}Context: {context}\nQuestion: {question}\nAnswer:"

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                pad_token_id=tokenizer.eos_token_id,
                temperature=0.1
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Отрезаем промпт и берем только ответ
        pred_answer = response[len(prompt):].split("\n")[0].strip()

        em_total += exact_match_score(pred_answer, true_answer)
        f1_total += f1_score(pred_answer, true_answer)
        count += 1

        if count % 10 == 0:
            print(f"Обработано {count} примеров...")

    return {"F1": round((f1_total / count) * 100, 2), "EM": round((em_total / count) * 100, 2)}


if __name__ == "__main__":
    BASE_MODEL = "meta-llama/Llama-3.2-1B"
    LORA_MODEL = "carozyyx/squad-llama-lora"  # ЗАМЕНИТЬ

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    # Берем 100 случайных примеров из валидации для скорости тестирования локально
    val_data = load_dataset("squad_v2", split="validation").shuffle(seed=42).select(range(100))

    # --- 1. Оценка Base Model (Zero-shot и Few-shot) ---
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL,
                                                      torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                                                      device_map="auto")

    zero_shot_res = evaluate_model(base_model, tokenizer, val_data, "Zero-shot", device)

    # Собираем 5 примеров для Few-shot (берем из тренировочного сета)
    few_shot_prompt = ""
    train_samples = load_dataset("squad_v2", split="train").select(range(5))
    for sample in train_samples:
        ans = sample['answers']['text'][0] if len(sample['answers']['text']) > 0 else "Unanswerable"
        few_shot_prompt += f"Context: {sample['context']}\nQuestion: {sample['question']}\nAnswer: {ans}\n\n"

    few_shot_res = evaluate_model(base_model, tokenizer, val_data, "Few-shot (5 примеров)", device,
                                  few_shot_examples=few_shot_prompt)

    # Очищаем память перед загрузкой LoRA
    del base_model
    torch.cuda.empty_cache() if device == "cuda" else None

    # --- 2. Оценка LoRA ---
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL,
                                                      torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                                                      device_map="auto")
    lora_model = PeftModel.from_pretrained(base_model, LORA_MODEL)

    lora_res = evaluate_model(lora_model, tokenizer, val_data, "LoRA Fine-tuned", device)

    # Вывод финальной таблицы
    print("\n\n3. Оценка (Финальные Результаты)")
    print("-" * 50)
    print(f"{'Метод':<25} | {'F1':<10} | {'Exact Match':<10}")
    print("-" * 50)
    print(f"{'Zero-shot':<25} | {zero_shot_res['F1']:<10} | {zero_shot_res['EM']:<10}")
    print(f"{'Few-shot (5 примеров)':<25} | {few_shot_res['F1']:<10} | {few_shot_res['EM']:<10}")
    print(f"{'LoRA':<25} | {lora_res['F1']:<10} | {lora_res['EM']:<10}")
    print("-" * 50)