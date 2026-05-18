from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, pipeline
import torch

model = AutoPeftModelForCausalLM.from_pretrained(
    "твой_логин/llama-3.2-1b-squad-lora",
    device_map="auto",
    torch_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained("твой_логин/llama-3.2-1b-squad-lora")

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=100)

def ask(question, context):
    prompt = f"""Context: {context}

Question: {question}

Answer:"""
    result = pipe(prompt)[0]['generated_text']
    return result.split("Answer:")[-1].strip()

# Пример
context = "Москва — столица России..."
print(ask("Какая столица России?", context))