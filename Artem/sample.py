import torch
import argparse
from bpe_tokenizer import BPE_Tokenizer
from model import GPT
from data import get_tokenizer

def parse_args():
    parser = argparse.ArgumentParser(description="LLM Sampling with Top-K & Temperature")
    parser.add_argument("--checkpoint", type=str, required=True, help="Путь к .pt файлу")
    parser.add_argument("--prompt", type=str, default="", help="Начальный текст")
    parser.add_argument("--max_new_tokens", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.8, help=">1 = креативнее, <1 = строже")
    parser.add_argument("--top_k", type=int, default=50, help="Оставляем только top_k вероятных токенов")
    parser.add_argument("--block_size", type=int, default=128, help="Должен совпадать с train.py")
    parser.add_argument("--device", type=str, default="cuda")
    return parser.parse_args()

def top_k_filtering(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    """Обнуляет вероятности для всех токенов, кроме top_k самых вероятных"""
    if top_k <= 0:
        return logits
    top_k = min(top_k, logits.size(-1))
    threshold = torch.topk(logits, top_k, dim=-1).values[..., -1, None]
    logits[logits < threshold] = float('-inf')
    return logits

def generate(model: GPT, idx: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int = 50) -> torch.Tensor:
    """Авторегрессионная генерация с ограничением контекста"""
    for _ in range(max_new_tokens):
        # Обрезаем до block_size, чтобы не превысить лимит модели
        idx_cond = idx[:, -model.block_size:]
        with torch.no_grad():
            logits = model(idx_cond)
            # Берём логиты только для последнего токена
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            logits = top_k_filtering(logits, top_k)
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx

def main():
    args = parse_args()
    device = torch.device(args.device)
    
    # Загрузка чекпоинта
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=True)
    
    # Инициализация токенизатора (загрузит сохранённый bpe_model.json)
    tokenizer = get_tokenizer()
    
    # Инициализация модели и загрузка весов
    model = GPT(
        vocab_size=tokenizer.vocab_size,
        n_embd=256, n_head=4, n_layer=4, 
        block_size=args.block_size
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    # Кодирование промпта
    prompt_ids = tokenizer.encode(args.prompt)
    x = torch.tensor(prompt_ids, dtype=torch.long, device=device).unsqueeze(0)
    
    print(f"🤖 Prompt: {args.prompt}")
    with torch.no_grad():
        out = generate(model, x, args.max_new_tokens, args.temperature, args.top_k)
        
    # Декодирование и вывод
    generated_text = tokenizer.decode(out[0].tolist())
    print(f"\n📝 Generated:\n{generated_text}")

if __name__ == "__main__":
    main()