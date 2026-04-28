import numpy as np
import argparse
import time
import json
from tqdm import tqdm
import matplotlib.pyplot as plt

from modules.transformer import TransformerLM
from utils.bpe_tokenizer import BPETokenizer
from utils.data import TextDataset, DataLoader
from utils.optim import Adam
from utils.loss import cross_entropy_loss

def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='data.txt')
    parser.add_argument('--val_split', type=float, default=0.1)
    parser.add_argument('--vocab_size', type=int, default=2000)
    parser.add_argument('--block_size', type=int, default=128)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--d_model', type=int, default=128)
    parser.add_argument('--n_layer', type=int, default=2)
    parser.add_argument('--n_head', type=int, default=4)
    parser.add_argument('--d_ff', type=int, default=256)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--save_path', type=str, default='model.npz')
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    print(" Загрузка данных...")
    text = load_data(args.data)
    
    print("🔤 Обучение токенизатора...")
    tokenizer = BPETokenizer(args.vocab_size)
    tokenizer.train(text)
    print(f"   Размер словаря: {tokenizer.vocab_len}")
    
    split_idx = int(len(text) * (1 - args.val_split))
    train_text, val_text = text[:split_idx], text[split_idx:]
    
    train_ds = TextDataset(train_text, tokenizer, args.block_size)
    val_ds = TextDataset(val_text, tokenizer, args.block_size)
    
    train_loader = DataLoader(train_ds, args.batch_size, shuffle=True, seed=args.seed)
    val_loader = DataLoader(val_ds, args.batch_size, shuffle=False, seed=args.seed)
    
    print("️ Инициализация модели...")
    model = TransformerLM(
        vocab_size=tokenizer.vocab_len,
        d_model=args.d_model,
        n_layer=args.n_layer,
        n_head=args.n_head,
        d_ff=args.d_ff,
        max_len=args.block_size,
        seed=args.seed
    )
    
    optimizer = Adam(model.get_params(), lr=args.lr)
    
    train_losses, val_losses = [], []
    
    print("🔥 Начало обучения...")
    for epoch in range(args.epochs):
        epoch_loss = 0
        start_time = time.time()
        
        for x_batch, y_batch in tqdm(train_loader, desc=f"Epoch {epoch+1} [train]"):
            logits = model.forward(x_batch)
            loss, grad_logits = cross_entropy_loss(logits, y_batch)
            
            model.zero_grad()
            model.backward(grad_logits)
            optimizer.step()
            
            epoch_loss += loss
        
        train_loss = epoch_loss / len(train_loader)
        train_losses.append(train_loss)
        
        val_loss = 0
        for x_batch, y_batch in val_loader:
            logits = model.forward(x_batch)
            loss, _ = cross_entropy_loss(logits, y_batch)
            val_loss += loss
        val_loss /= len(val_loader)
        val_losses.append(val_loss)
        
        epoch_time = time.time() - start_time
        print(f"Epoch {epoch+1}/{args.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Time: {epoch_time:.1f}s")
    
    print(f"💾 Сохранение модели в {args.save_path}...")
    save_dict = {}
    for param, grad, name in model.get_params():
        save_dict[name] = param
    np.savez(args.save_path, **save_dict)
    
    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Progress')
    plt.legend()
    plt.grid(True)
    plt.savefig('loss_curve.png')
    print("📈 График сохранён в loss_curve.png")
    
    with open('config.json', 'w') as f:
        json.dump(vars(args), f, indent=2)

if __name__ == '__main__':
    train()