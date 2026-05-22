import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_local_inference(base_model_id: str, peft_model_id: str):
    print("Загрузка токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)

    print("Загрузка базовой модели (CPU/GPU)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto"
    )

    print("Применение LoRA адаптеров...")
    model = PeftModel.from_pretrained(base_model, peft_model_id)
    return model, tokenizer, device


def ask_question(model, tokenizer, device, context: str, question: str) -> str:
    prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=30,
            pad_token_id=tokenizer.eos_token_id,
            temperature=0.1
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Извлекаем только то, что модель сгенерировала после "Answer:"
    answer = response.split("Answer:")[-1].strip()
    return answer


if __name__ == "__main__":
    BASE = "meta-llama/Llama-3.2-1B"
    # Замени на имя своей модели из Hub
    LORA = "carozyyx/squad-llama-lora"

    model, tokenizer, device = load_local_inference(BASE, LORA)

    test_context = "PyCharm 2025.3.2 is an IDE developed by JetBrains. It fully supports modern Python 3.14 features."
    test_question = "Who developed PyCharm 2025.3.2?"

    ans = ask_question(model, tokenizer, device, test_context, test_question)
    print(f"\nВопрос: {test_question}\nОтвет модели: {ans}")