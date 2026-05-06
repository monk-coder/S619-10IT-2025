import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

MODEL_PATH = "./llama-squad-lora-adapter"  # Путь к скачанному адаптеру или HF repo
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    torch_dtype=torch.float16,
    device_map=DEVICE
)
model = PeftModel.from_pretrained(base_model, MODEL_PATH)
model.eval()

def ask(question, context):
    prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=32, do_sample=False, 
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(out[0], skip_special_tokens=True).split("Answer:")[-1].strip()

# 3 примера из val
samples = [
    ("What year did the Super Bowl 50 take place?", 
     "Super Bowl 50 was an American football game to determine the champion of the National Football League (NFL) for the 2015 season. The American Football Conference (AFC) champion Denver Broncos defeated the National Football Conference (NFC) champion Carolina Panthers 24–10 to earn their third Super Bowl title. The game was played on February 7, 2016."),
    ("Who wrote the play 'Romeo and Juliet'?",
     "Romeo and Juliet is a tragedy written by William Shakespeare early in his career about two young star-crossed lovers whose deaths ultimately reconcile their feuding families."),
    ("What is the capital of France?",
     "France, officially the French Republic, is a country primarily located in Western Europe. Its capital and most populous city is Paris.")
]

for q, c in samples:
    print(f"Q: {q}")
    print(f"A: {ask(q, c)}\n{'-'*50}")