# ============================================
# ЯЧЕЙКА 11: Zero-shot оценка
# ============================================
print("=== ZERO-SHOT ОЦЕНКА ===")

# Загружаем базовую модель без обучения
from transformers import pipeline

generator = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B",
    device_map="auto",
    torch_dtype=torch.bfloat16
)


def zero_shot_qa(context, question):
    prompt = f"""Answer the question based only on the context.

Context: {context}

Question: {question}

Answer:"""

    result = generator(
        prompt,
        max_new_tokens=50,
        temperature=0.1,
        do_sample=False
    )

    answer = result[0]["generated_text"][len(prompt):].strip()
    # Берем первую строку как ответ
    answer = answer.split('\n')[0]
    return answer


# Оценка zero-shot на 100 примерах
predictions_zs = []
for i, example in enumerate(dataset["validation"].select(range(100))):
    pred = zero_shot_qa(example["context"], example["question"])
    predictions_zs.append({
        "id": example["id"],
        "prediction_text": pred
    })

results_zs = squad_metric.compute(predictions=predictions_zs, references=references)
print(f"Zero-shot - EM: {results_zs['exact_match']:.2f}%, F1: {results_zs['f1']:.2f}%")