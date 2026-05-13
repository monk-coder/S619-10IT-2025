# Cell 2: Обучение (С предварительной токенизацией — надёжно!)
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
import os

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "./squad-qwen-lora-cpu"
MAX_STEPS = 50
MAX_LENGTH = 256  # Явно задаём длину

print(f"🚀 Обучение: {MODEL_NAME} | Steps: {MAX_STEPS}")

# 1. Данные
squad = load_dataset("squad_v2", split="train[:500]")
PROMPT = "Context: {context}\nQuestion: {question}\nAnswer: {answer}"

def format_sample(ex):
    ans = ex["answers"]["text"][0] if ex["answers"]["text"] else "unknown"
    return PROMPT.format(context=ex["context"], question=ex["question"], answer=ans)

# 2. Токенизатор
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

# 🔧 3. Предварительная токенизация (ключевое исправление!)
def tokenize_function(examples):
    # examples — это список строк, т.к. мы вернули строку из format_sample
    texts = [format_sample({"context": c, "question": q, "answers": {"text": [a] if a else []}}) 
             for c, q, a in zip(examples["context"], examples["question"], 
                               [ans["text"][0] if ans["text"] else "unknown" for ans in examples["answers"]])]
    
    return tokenizer(
        texts,
        truncation=True,
        padding=False,  # Паддинг сделает коллатор
        max_length=MAX_LENGTH
    )

tokenized_dataset = squad.map(
    tokenize_function,
    batched=True,
    remove_columns=squad.column_names,  # Убираем старые колонки
    desc="Токенизация..."
)

# 4. Модель
print("📦 Загрузка модели...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32,
    attn_implementation="eager",
    device_map=None
)

# 5. LoRA
lora_config = LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 6. Настройки
args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_steps=50,
    max_steps=MAX_STEPS,
    logging_steps=10,
    save_steps=MAX_STEPS,
    save_total_limit=1,
    fp16=False,
    report_to="none",
    dataloader_num_workers=0
)

# 7. Коллатор для уже токенизированных данных
collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# 8. Запуск Trainer (минимум аргументов — данные уже готовы)
trainer = SFTTrainer(
    model=model,
    args=args,
    train_dataset=tokenized_dataset,  # ✅ Уже токенизированный датасет
    data_collator=collator
)

print("⏱️  Начало обучения...")
trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ Сохранено: {OUTPUT_DIR}")