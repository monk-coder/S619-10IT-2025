# train.py
import os, math, time, sys, itertools
import torch
from torch.optim import AdamW
from torch.amp import autocast, GradScaler
from config import parse_train_args
from data import load_data, get_tokenizer
from model import GPT

def cosine_warmup(optimizer, warmup_steps, total_steps):
    def lr_lambda(step):
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

def main():
    print("🚀 Инициализация...", flush=True)
    args = parse_train_args()
    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    print(f"📌 Устройство: {device} | Max Iters: {args.max_iters}", flush=True)

    # Оптимизации для CPU
    if device.type == 'cpu':
        torch.set_num_threads(max(1, os.cpu_count() // 2))
        torch.set_float32_matmul_precision('high')

    print("📦 Загрузка данных и токенизатора...", flush=True)
    tokenizer = get_tokenizer(args.data_file)
    train_dl, val_dl, _ = load_data(args.data_file, tokenizer, args.block_size, args.batch_size)
    vocab_size = tokenizer.vocab_size
    print(f"📊 Словарь: {vocab_size} | Батчей в эпохе: {len(train_dl)}", flush=True)

    model = GPT(vocab_size=vocab_size, n_embd=256, n_head=4, n_layer=4, block_size=args.block_size).to(device)
    optimizer = AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
    scheduler = cosine_warmup(optimizer, int(args.max_iters * args.warmup_ratio), args.max_iters)

    # ⚠️ AMP и GradScaler ТОЛЬКО для CUDA. На CPU они часто вешают процесс.
    use_amp = device.type == 'cuda'
    scaler = GradScaler(enabled=use_amp)

    os.makedirs("checkpoints", exist_ok=True)
    best_val_loss, best_step = float("inf"), 0
    start_time = time.time()

    train_iter = itertools.cycle(train_dl)
    print("🔄 Цикл обучения запущен...", flush=True)

    for step in range(1, args.max_iters + 1):
        x, y = next(train_iter)
        x, y = x.to(device, non_blocking=use_amp), y.to(device, non_blocking=use_amp)

        optimizer.zero_grad(set_to_none=True)
        
        # Автокаст только если GPU
        with torch.autocast(device_type=device.type, enabled=use_amp):
            logits = model(x)
            loss = torch.nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))

        if use_amp:
            scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()

        scheduler.step()

        if step % args.eval_interval == 0 or step == 1:
            model.eval()
            val_losses = []
            with torch.no_grad():
                for vx, vy in val_dl:
                    vx, vy = vx.to(device), vy.to(device)
                    vlogits = model(vx)
                    vloss = torch.nn.functional.cross_entropy(vlogits.view(-1, vlogits.size(-1)), vy.view(-1))
                    val_losses.append(vloss.item())
            model.train()
            
            val_loss = sum(val_losses) / len(val_losses)
            ppl = math.exp(min(val_loss, 100))
            elapsed = time.time() - start_time
            print(f"step {step:5d} | loss {loss.item():.4f} | val_loss {val_loss:.4f} | ppl {ppl:.2f} | lr {optimizer.param_groups[0]['lr']:.2e} | {step/elapsed:.2f} it/s", flush=True)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_step = step
                torch.save({
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "step": step,
                    "val_loss": val_loss
                }, "checkpoints/best.pt")
                print("  ✅ Сохранён лучший чекпоинт", flush=True)

    print(f"🏁 Обучение завершено. Лучший шаг: {best_step}, Val Loss: {best_val_loss:.4f}", flush=True)

if __name__ == "__main__":
    main()