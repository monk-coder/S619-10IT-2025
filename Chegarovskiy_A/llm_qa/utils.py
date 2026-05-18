import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed as hf_set_seed
from peft import PeftModel
from config import BASE_MODEL_NAME, ADAPTER_PATH, MAX_NEW_TOKENS, PROMPT_TEMPLATE, SYSTEM_MESSAGE


def set_seed(seed: int = 42):
    hf_set_seed(seed)


def load_model_and_tokenizer(base_model_name=BASE_MODEL_NAME, adapter_path=ADAPTER_PATH):
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Загружаем на CPU для локального инференса
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="cpu",
        torch_dtype=torch.float32
    )

    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)

    model.eval()
    return model, tokenizer


def ask_question(model, tokenizer, context: str, question: str) -> str:
    prompt = PROMPT_TEMPLATE.format(SYSTEM_MESSAGE=SYSTEM_MESSAGE, context=context, question=question)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )

    decoded = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return decoded.strip().lower()