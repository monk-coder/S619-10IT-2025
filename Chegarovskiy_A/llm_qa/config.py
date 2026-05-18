import torch

# --- Модель и пути ---
BASE_MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct" # зеркало
ADAPTER_PATH = "adrianchega/llama-squad-results"

# --- Конфигурация LoRA ---
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# --- Гиперпараметры обучения (оставляем для отчета) ---
MAX_STEPS = 500
BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 1e-4
WARMUP_STEPS = 50
MAX_SEQ_LENGTH = 1024

# --- Инференс ---
MAX_NEW_TOKENS = 64
SAMPLE_SIZE = 50

# --- Интеллектуальный выбор устройства для ПК ---
if torch.cuda.is_available():
    DEVICE = "cuda"
    ATTN_IMPLEMENTATION = "flash_attention_2" if torch.cuda.get_device_capability()[0] >= 8 else "sdpa"
elif torch.backends.mps.is_available():
    DEVICE = "mps"
    ATTN_IMPLEMENTATION = "sdpa"
else:
    DEVICE = "cpu"
    ATTN_IMPLEMENTATION = "sdpa"

# --- Промпт-инжиниринг ---
SYSTEM_MESSAGE = "You are a helpful assistant that answers questions based on context. Answer the question as briefly as possible. If the answer is not in the context, output only the word 'unanswerable'."

PROMPT_TEMPLATE = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_MESSAGE}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nContext: {context}\nQuestion: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"