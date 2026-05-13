import torch

BASE_MODEL_NAME = "./phi2-model"
ADAPTER_PATH = "./phi2-squad-lora-final"
ATTN_IMPLEMENTATION = "sdpa"

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "v_proj"]
MAX_STEPS = 500
BATCH_SIZE = 4
LEARNING_RATE = 2e-4
WARMUP_STEPS = 50
MAX_SEQ_LENGTH = 1024

MAX_NEW_TOKENS = 50
SAMPLE_SIZE = 3

if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")

SYSTEM_MESSAGE = "You are a precise assistant for question answering. Answer the question based ONLY on the provided context. If the answer cannot be found in the context, output exactly 'unanswerable'."

PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{SYSTEM_MESSAGE}<|eot_id|><|start_header_id|>user<|end_header_id|>
Context: {context}
Question: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""