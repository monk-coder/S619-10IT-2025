import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import argparse
from model import MiniLLM
from data import get_dataloaders
from config import Config
import os
from tqdm import tqdm

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--eval_interval', type=int, default=200)
    args = parser.parse_args()

    config = Config()
    config.batch_size = args.batch_size
    config.eval_interval = args.eval_interval

    train_loader, val_loader, vocab_size = get_dataloaders(batch_size=config.batch_size)
    config.vocab_size = vocab_size

    model = MiniLLM(config).to(config.device)
    optimizer = AdamW(model.parameters(), lr=config.learning_rate, 
                     weight_decay=config.weight_decay, betas=(config.beta1, config.beta2))
    
    scheduler = CosineAnnealingLR(optimizer, T_max=config.max_iters, eta_min=1e-5)
    
    best_val_loss = float('inf')
    
    for iter in tqdm(range(config.max_iters)):
        model.train()
        xb, yb = next(iter(train_loader))
        xb, yb = xb.to(config.device), yb.to(config.device)
        
        logits = model(xb)
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), yb.view(-1))
        
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
        optimizer.step()
        scheduler.step()

        if iter % config.eval_interval == 0:
            model.eval()
            val_loss = 0
            with torch.no_grad():
                for xb, yb in val_loader:
                    xb, yb = xb.to(config.device), yb.to(config.device)
                    logits = model(xb)
                    val_loss += F.cross_entropy(logits.view(-1, logits.size(-1)), yb.view(-1)).item()
            val_loss /= len(val_loader)
            
            print(f"Step {iter}: Train Loss {loss.item():.4f} | Val Loss {val_loss:.4f} | PPL {torch.exp(torch.tensor(val_loss)):.2f}")
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), "checkpoints/best_model.pt")

if name == "main":
    os.makedirs("checkpoints", exist_ok=True)
    train()