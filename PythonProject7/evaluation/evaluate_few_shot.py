# ============================================
# ЯЧЕЙКА 12: Few-shot оценка (5 примеров)
# ============================================
from transformers import pipeline
print("\n=== FEW-SHOT ОЦЕНКА (5 примеров) ===")

# Берем 5 примеров из train
few_shot_examples = []
for i in range(5):
    ex = dataset["train"][i]
    if ex["answers"]["text"]:
        few_shot_examples.append({
            "context": ex["context"],
            "question": ex["question"],
            "answer": ex["answers"]["text"][0]
        })


def few_shot_qa(context, question):
    prompt = "Answer the questions based on the contexts.\n\n"

    # Добавляем примеры
    for ex in few_shot_examples:
        prompt += f"Context: {ex['context']}\n"
        prompt += f"Question: {ex['question']}\n"
        prompt += f"Answer: {ex['answer']}\n\n"

    # Добавляем тестовый вопрос
    prompt += f"Context: {context}\n"
    prompt += f"Question: {question}\n"
    prompt += f"Answer:"

    result = generator(
        prompt,
        max_new_tokens=50,
        temperature=0.1,
        do_sample=False
    )

    answer = result[0]["generated_text"][len(prompt):].strip()
    answer = answer.split('\n')[0]
    return answer


# Оценка few-shot
predictions_fs = []
for i, example in enumerate(dataset["validation"].select(range(100))):
    pred = few_shot_qa(example["context"], example["question"])
    predictions_fs.append({
        "id": example["id"],
        "prediction_text": pred
    })

results_fs = squad_metric.compute(predictions=predictions_fs, references=references)
print(f"Few-shot - EM: {results_fs['exact_match']:.2f}%, F1: {results_fs['f1']:.2f}%")