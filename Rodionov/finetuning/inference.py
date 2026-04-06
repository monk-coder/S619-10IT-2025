import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import argparse


def load_model(base_model_name="meta-llama/Llama-3.2-1B", lora_path="./lora-squad-model"):
    """Загрузка модели с LoRA весами"""
    print(f"Loading base model: {base_model_name}")

    # Загрузка токенизатора
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Загрузка модели (локально, без quantization)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Загрузка LoRA адаптера
    model = PeftModel.from_pretrained(model, lora_path)
    model.eval()

    return model, tokenizer


def predict_answer(context, question, model, tokenizer, max_length=128):
    """Получение ответа от модели"""
    # Форматирование промпта
    prompt = f"""Context: {context}
Question: {question}
Answer: """

    # Токенизация
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    ).to(model.device)

    # Генерация
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # Декодирование ответа
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Извлечение ответа после "Answer: "
    answer = full_response.split("Answer: ")[-1].strip()

    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=str, help="Context for QA")
    parser.add_argument("--question", type=str, help="Question to answer")
    parser.add_argument("--lora_path", type=str, default="./lora-squad-model", help="Path to LoRA weights")
    args = parser.parse_args()

    # Загрузка модели
    model, tokenizer = load_model(lora_path=args.lora_path)

    # Примеры вопросов из validation set (для демонстрации)
    examples = [
        {
            "context": "The Colosseum is an oval amphitheatre in the centre of Rome, Italy. Built of concrete and sand, it is the largest amphitheatre ever built.",
            "question": "Where is the Colosseum located?"
        },
        {
            "context": "Machine learning is a subset of artificial intelligence that enables systems to learn from data. Deep learning is a subset of machine learning using neural networks.",
            "question": "What is deep learning a subset of?"
        },
        {
            "context": "The Amazon rainforest, also known as Amazonia, is a moist broadleaf tropical rainforest in the Amazon biome that covers most of the Amazon basin of South America.",
            "question": "What is another name for the Amazon rainforest?"
        }
    ]

    print("\n" + "=" * 50)
    print("Running inference on 3 examples:")
    print("=" * 50 + "\n")

    for i, example in enumerate(examples, 1):
        print(f"Example {i}:")
        print(f"Context: {example['context'][:100]}...")
        print(f"Question: {example['question']}")

        answer = predict_answer(example["context"], example["question"], model, tokenizer)

        print(f"Answer: {answer}")
        print("-" * 50 + "\n")

    # Если передан аргумент через командную строку
    if args.context and args.question:
        print("Custom query:")
        print(f"Context: {args.context}")
        print(f"Question: {args.question}")
        answer = predict_answer(args.context, args.question, model, tokenizer)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()