# train.py
import os
import sys
import time
import torch
import torch.nn as nn
from tqdm import tqdm

from config import parse_args, setup_config
from model import TransformerLM
from data import get_dataloaders

def estimate_loss(model, val_loader, device, dtype, eval_iters=10):
    model.eval()
    losses = []
    
    with torch.no_grad():
        for _ in range(eval_iters):
            try:
                x_batch, y_batch = next(val_iter)
            except:
                val_iter = iter(val_loader)
                x_batch, y_batch = next(val_iter)
            
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)
            
            # Autocast для mixed precision
            if device != 'cpu' and dtype != torch.float32:
                with torch.amp.autocast(device_type='cuda' if device == 'cuda' else 'cpu', dtype=dtype):
                    _, loss = model(x_batch, y_batch)
            else:
                _, loss = model(x_batch, y_batch)
            
            losses.append(loss.item())
    
    model.train()
    return sum(losses) / len(losses)

def main():
    args = parse_args()
    args = setup_config(args)
    
    print(f"🚀 Starting training on {args.device} with {args.dtype}")
    print(f"📦 Model: d_model={args.d_model}, n_heads={args.n_heads}, n_layers={args.n_layers}")
    
    # Data
    train_loader, val_loader, tokenizer = get_dataloaders(
        args.data, args.tokenizer, args.batch_size, args.block_size
    )
    if train_loader is None:
        sys.exit(1)
    
    # Model
    model = TransformerLM(
        vocab_size=tokenizer.vocab_len,
        block_size=args.block_size,
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        d_ff=args.d_ff,
        dropout=args.dropout
    ).to(args.device)
    
    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=args.lr, 
        weight_decay=args.weight_decay,
        betas=(0.9, 0.95)
    )
    
    # Scheduler (linear warmup + cosine decay)
    def get_lr(it):
        if it < 100:
            return args.lr * it / 100
        if it > args.max_iters:
            return args.lr * 0.1
        return args.lr * 0.5 * (1 + torch.cos(torch.tensor((it - 100) / (args.max_iters - 100) * 3.14159)))
    
    # Training loop
    best_val_loss = float('inf')
    iter_num = 0
    val_iter = iter(val_loader)
    
    print(f"📈 Training for {args.max_iters} iterations...")
    
    while iter_num < args.max_iters:
        for x_batch, y_batch in train_loader:
            if iter_num >= args.max_iters:
                break
            
            x_batch = x_batch.to(args.device)
            y_batch = y_batch.to(args.device)
            
            # Forward + backward
            optimizer.zero_grad(set_to_none=True)
            
            if args.device != 'cpu' and args.torch_dtype != torch.float32:
                with torch.amp.autocast(device_type='cuda' if args.device == 'cuda' else 'cpu', dtype=args.torch_dtype):
                    _, loss = model(x_batch, y_batch)
            else:
                _, loss = model(x_batch, y_batch)
            
            loss.backward()
            
            # Gradient clipping
            if args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            
            # Learning rate schedule
            for param_group in optimizer.param_groups:
                param_group['lr'] = get_lr(iter_num)
            
            optimizer.step()
            
            # Logging
            if iter_num % args.eval_interval == 0 or iter_num == args.max_iters - 1:
                train_loss = loss.item()
                val_loss = estimate_loss(model, val_loader, args.device, args.torch_dtype, args.eval_iters)
                
                print(f"iter {iter_num}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, lr={get_lr(iter_num):.2e}")
                
                # Save checkpoint
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    checkpoint = {
                        'model': model.state_dict(),
                        'tokenizer': tokenizer,
                        'args': args,
                        'iter_num': iter_num,
                        'val_loss': best_val_loss,
                    }
                    ckpt_path = os.path.join(args.out_dir, 'ckpt_best.pt')
                    torch.save(checkpoint, ckpt_path)
                    print(f"💾 Saved best checkpoint: {ckpt_path}")
            
            iter_num += 1
    
    print("✅ Training complete!")

if __name__ == '__main__':
    main()