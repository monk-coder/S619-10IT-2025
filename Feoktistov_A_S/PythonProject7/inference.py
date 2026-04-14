# ============================================
# inference.py - запускать на локальном ПК
# ============================================
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
from peft import PeftModel


def predict_answer(model, tokenizer, context, question):
    """Предсказание ответа на вопрос"""
    inputs = tokenizer(
        question,
        context,
        return_tensors="pt",
        truncation=True,
        max_length=384
    )

    with torch.no_grad():
        outputs = model(**inputs)

    start_idx = torch.argmax(outputs.start_logits)
    end_idx = torch.argmax(outputs.end_logits)

    if start_idx > end_idx:
        return ""

    answer_ids = inputs["input_ids"][0][start_idx:end_idx + 1]
    answer = tokenizer.decode(answer_ids, skip_special_tokens=True)
    return answer if answer else "No answer found"


def main():
    print("Загрузка модели...")

    # Загружаем базовую модель
    base_model = AutoModelForQuestionAnswering.from_pretrained(
        "meta-llama/Llama-3.2-1B",
        device_map="cpu"  # На CPU для локального запуска
    )

    # Загружаем LoRA адаптер с Hugging Face
    model = PeftModel.from_pretrained(
        base_model,
        "ваш-username/llama-3.2-1b-squad-lora"  # Замените на ваш username
    )

    tokenizer = AutoTokenizer.from_pretrained("ваш-username/llama-3.2-1b-squad-lora")

    # Тестовые вопросы (из валидационной выборки)
    test_samples = [
        {
            "context": "Paris is the capital of France. The Eiffel Tower is located in Paris.",
            "question": "What is the capital of France?",
            "expected": "Paris"
        },
        {
            "context": "Machine learning is a subset of artificial intelligence. Deep learning is a subset of machine learning.",
            "question": "What is a subset of artificial intelligence?",
            "expected": "Machine learning"
        },
        {
            "context": "The first moon landing was in 1969 by Apollo 11. Neil Armstrong was the first person to walk on the moon.",
            "question": "Who was the first person to walk on the moon?",
            "expected": "Neil Armstrong"
        }
    ]

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ НА 3 ВОПРОСАХ")
    print("=" * 60)

    for i, sample in enumerate(test_samples, 1):
        print(f"\nВопрос {i}:")
        print(f"Context: {sample['context'][:100]}...")
        print(f"Question: {sample['question']}")

        prediction = predict_answer(model, tokenizer, sample['context'], sample['question'])

        print(f"Predicted answer: {prediction}")
        print(f"Expected answer: {sample['expected']}")
        print(f"Correct: {'✓' if prediction.lower() == sample['expected'].lower() else '✗'}")
        print("-" * 40)


if __name__ == "__main__":
    main()