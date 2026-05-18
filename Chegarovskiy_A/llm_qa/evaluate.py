import re, string
from tqdm import tqdm
from datasets import load_dataset
from utils import load_model_and_tokenizer, ask_question, set_seed
from config import SAMPLE_SIZE


def normalize_answer(s):
    """Официальная нормализация из SQuAD scripts."""

    def remove_articles(text): return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text): return ' '.join(text.split())

    def remove_punc(text): return ''.join(ch for ch in text if ch not in set(string.punctuation))

    def lower(text): return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s):
    if not s: return []
    return normalize_answer(s).split()


def compute_metrics(prediction, gold_answers):
    if not gold_answers or gold_answers == ["unanswerable"]:
        return (1.0, 1.0) if prediction == "unanswerable" else (0.0, 0.0)

    if prediction == "unanswerable":
        return (0.0, 0.0)

    f1_scores = []
    em_scores = []

    for gold in gold_answers:
        norm_gold = normalize_answer(gold)
        norm_pred = normalize_answer(prediction)

        em_scores.append(float(norm_gold == norm_pred))

        gold_tokens = get_tokens(gold)
        pred_tokens = get_tokens(prediction)
        common = set(gold_tokens) & set(pred_tokens)
        num_same = len(common)

        if num_same == 0:
            f1_scores.append(0.0)
            continue

        precision = num_same / len(pred_tokens)
        recall = num_same / len(gold_tokens)
        f1_scores.append((2 * precision * recall) / (precision + recall))

    return max(f1_scores), max(em_scores)


def main():
    set_seed()
    print("Загрузка модели для расчета метрик...")
    model, tokenizer = load_model_and_tokenizer()
    dataset = load_dataset("squad_v2", split="validation").select(range(SAMPLE_SIZE))

    total_f1, total_em = 0, 0

    print(f"\nВычисляем метрики для {SAMPLE_SIZE} примеров...")
    for ex in tqdm(dataset):
        gold_answers = ex['answers']['text'] if ex['answers']['text'] else ["unanswerable"]
        prediction = ask_question(model, tokenizer, ex['context'], ex['question'])

        f1, em = compute_metrics(prediction, gold_answers)
        total_f1 += f1
        total_em += em

    print(f"\n--- Итоговые результаты (N={SAMPLE_SIZE}) ---")
    print(f"F1: {total_f1 / SAMPLE_SIZE * 100:.2f}%")
    print(f"EM: {total_em / SAMPLE_SIZE * 100:.2f}%")


if __name__ == "__main__":
    main()