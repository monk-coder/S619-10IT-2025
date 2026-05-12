import os
import math
import time
import torch
from config import get_config
from model import TransformerLM
from data import get_dataloaders

def get_cosine_lr(it, max_iters, warmup_iters, lr):
    if it < warmup_iters:
        return lr * (it + 1) / warmup_iters
    if it > max_iters:
        return lr * 0.0
    decay_ratio = (it - warmup_iters) / (max_iters - warmup_iters)
    return 0.5 * lr * (1.0 + math.cos(math.pi * decay_ratio))

def train(cfg):
    torch.manual_seed(cfg.seed)
    device = cfg.device if torch.cuda.is_available() and cfg.device == 'cuda' else 'cpu'
    dtype = torch.float16 if cfg.dtype == 'float16' else torch.bfloat16 if cfg.dtype == 'bfloat16' else torch.float32
    
    print(f"Device: {device} | Dtype: {dtype} | Batch: {cfg.batch_size}")
    
    train_dl, val_dl, tokenizer = get_dataloaders(cfg.data, cfg.tokenizer_path, cfg.batch_size, cfg.block_size, cfg.seed)
    model = TransformerLM(tokenizer.vocab_len, cfg.block_size, d_model=128, n_heads=4, n_layers=2, d_ff=512, dropout=0.1).to(device)
    
    optimizer = model.configure_optimizers(cfg.lr, cfg.weight_decay, cfg.beta1, cfg.beta2)
    scaler = torch.amp.GradScaler(enabled=(device == 'cuda' and dtype == torch.float16))

    os.makedirs(cfg.checkpoint_dir, exist_ok=True)
    best_val_loss = float('inf')
    iter_num = 0
    t0 = time.time()

    train_iter = iter(train_dl)
    while iter_num < cfg.max_iters:
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_dl)
            x, y = next(train_iter)
            
        x, y = x.to(device), y.to(device)
        
        # Cosine LR with warmup
        lr = get_cosine_lr(iter_num, cfg.max_iters, cfg.warmup_iters, cfg.lr)
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

        with torch.amp.autocast(device_type=device, dtype=dtype, enabled=(device != 'cpu')):
            logits, loss = model(x, y)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)

        if iter_num % cfg.eval_interval == 0:
            t1 = time.time()
            dt = t1 - t0
            t0 = t1
            
            # Eval loop
            if val_dl is not None:
                model.eval()
                val_losses = []
                with torch.no_grad():
                    val_iter = iter(val_dl)
                    for _ in range(cfg.eval_iters):
                        vx, vy = next(val_iter, (None, None))
                        if vx is None:
                            val_iter = iter(val_dl)
                            vx, vy = next(val_iter)
                        vx, vy = vx.to(device), vy.to(device)
                        with torch.amp.autocast(device_type=device, dtype=dtype, enabled=(device != 'cpu')):
                            _, val_loss = model(vx, vy)
                        val_losses.append(val_loss.item())
                
                val_loss = sum(val_losses) / len(val_losses)
                val_ppl = math.exp(val_loss)
                print(f"iter {iter_num}: train_loss={loss.item():.4f} | val_loss={val_loss:.4f} | val_ppl={val_ppl:.2f} | lr={lr:.2e} | {dt:.2f}s")
            else:
                val_loss = loss.item()
                val_ppl = math.exp(val_loss)
                print(f"iter {iter_num}: train_loss={loss.item():.4f} | val_loss=N/A (skip) | val_ppl={val_ppl:.2f} | lr={lr:.2e} | {dt:.2f}s")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                ckpt = {
                    'model': model.state_dict(),
                    'optimizer': optimizer.state_dict(),
                    'config': cfg,
                    'tokenizer': tokenizer,
                    'best_val_loss': best_val_loss,
                    'iter': iter_num
                }
                torch.save(ckpt, os.path.join(cfg.checkpoint_dir, 'ckpt_best.pt'))
            model.train()

        iter_num += 1

    # Финальный чекпоинт
    torch.save({'model': model.state_dict(), 'tokenizer': tokenizer, 'config': cfg},
               os.path.join(cfg.checkpoint_dir, 'ckpt_final.pt'))
    print("✅ Training complete.")

if __name__ == '__main__':
    cfg = get_config()
    train(cfg)