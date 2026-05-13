import random
import numpy as np
import torch
from typing import Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed as hf_set_seed
from config import BASE_MODEL_NAME, DEVICE, MAX_NEW_TOKENS, PROMPT_TEMPLATE, SYSTEM_MESSAGE


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    hf_set_seed(seed)


def load_model_and_tokenizer(base_model_name: str = BASE_MODEL_NAME):
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    model.eval()
    return model, tokenizer


def ask_question(model, tokenizer, context: str, question: str) -> str:
    prompt = PROMPT_TEMPLATE.format(
        SYSTEM_MESSAGE=SYSTEM_MESSAGE,
        context=context,
        question=question
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_length = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_tokens = outputs[0][input_length:]
    answer = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    return answer