import torch
from config import parse_sample_args
from data import get_tokenizer
from model import GPT

def top_k_filtering(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    if top_k <= 0:
        return logits
    top_k = min(top_k, logits.size(-1))
    threshold = torch.topk(logits, top_k, dim=-1).values[..., -1, None]
    logits[logits < threshold] = float('-inf')
    return logits

def generate(model: GPT, idx: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int = 50) -> torch.Tensor:
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -model.block_size:]
        with torch.no_grad():
            logits = model(idx_cond)
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            logits = top_k_filtering(logits, top_k)
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx

def main():
    print("🚀 Инициализация генерации...", flush=True)
    args = parse_sample_args()
    device = torch.device(args.device)

    print(f"📥 Загрузка чекпоинта: {args.checkpoint}", flush=True)
    # Безопасная загрузка с автоматическим маппингом на CPU/GPU
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=True)

    print("🔤 Загрузка токенизатора...", flush=True)
    tokenizer = get_tokenizer()

    print("🏗 Инициализация модели...", flush=True)
    model = GPT(
        vocab_size=tokenizer.vocab_size,
        n_embd=256, n_head=4, n_layer=4,
        block_size=args.block_size
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    x = torch.tensor(prompt_ids, dtype=torch.long, device=device).unsqueeze(0)

    print(f"🤖 Промпт: {args.prompt}", flush=True)
    with torch.no_grad():
        out = generate(model, x, args.max_new_tokens, args.temperature, args.top_k)

    generated_text = tokenizer.decode(out[0].tolist())
    print(f"\n📝 Результат:\n{generated_text}", flush=True)

if __name__ == "__main__":
    main()
