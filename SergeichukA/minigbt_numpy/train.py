import numpy as np
import matplotlib
matplotlib.use('Agg')  # Отключает GUI-бэкенд, предотвращает зависание в Windows
import matplotlib.pyplot as plt
import argparse
import pickle
import os

from tokenizer import BPETokenizer
from transformer import TransformerLM
from data import TextDataset
from utils import cross_entropy_loss

def train(model, dataset, val_dataset, epochs, batch_size, lr, log_every=10):
    train_losses, val_losses = [], []
    
    for epoch in range(epochs):
        model.training = True
        epoch_loss = 0.0
        n_batches = max(1, len(dataset) // batch_size)
        
        print(f"\n🔹 Epoch {epoch+1}/{epochs} | Batches: {n_batches}")
        for i in range(n_batches):
            indices = np.random.randint(0, len(dataset), batch_size)
            X, Y = dataset.get_batch(indices, batch_size)
            
            logits = model.forward(X)
            loss = cross_entropy_loss(logits, Y, model.vocab_size)
            
            model.backward(logits, Y)
            model.update_params(lr)
            
            epoch_loss += loss
            print(f"   Batch {i+1}/{n_batches} | Loss: {loss:.4f}", end="\r")
            
        avg_loss = epoch_loss / n_batches
        train_losses.append(avg_loss)
        print(f"\n   ✅ Avg Loss: {avg_loss:.4f}")
        
        if val_dataset is not None and len(val_dataset) > 0:
            model.training = False
            val_loss = 0.0
            n_val = max(1, min(10, len(val_dataset) // batch_size))
            for i in range(n_val):
                indices = np.random.randint(0, len(val_dataset), batch_size)
                X_val, Y_val = dataset.get_batch(indices, batch_size)
                logits_val = model.forward(X_val)
                val_loss += cross_entropy_loss(logits_val, Y_val, model.vocab_size)
            val_losses.append(val_loss / n_val)
            
        if (epoch + 1) % log_every == 0:
            msg = f'Epoch {epoch+1}: train_loss={avg_loss:.4f}'
            if val_losses:
                msg += f', val_loss={val_losses[-1]:.4f}'
            print(msg)
            
    return train_losses, val_losses

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='data.txt')
    parser.add_argument('--vocab_size', type=int, default=3000)
    parser.add_argument('--block_size', type=int, default=128)
    parser.add_argument('--d_model', type=int, default=128)
    parser.add_argument('--n_heads', type=int, default=4)
    parser.add_argument('--n_layers', type=int, default=2)
    parser.add_argument('--d_ff', type=int, default=512)
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    with open(args.data, 'r', encoding='utf-8') as f:
        text = f.read()
        
    tokenizer = BPETokenizer(vocab_size=args.vocab_size)
    tokenizer.train(text)
    print(f'Vocab size: {tokenizer.vocab_len}')
    
    dataset = TextDataset(text, tokenizer, args.block_size)
    if len(dataset) == 0:
        print("❌ Датасет пуст! Увеличьте data.txt или уменьшите block_size.")
        return
        
    model = TransformerLM(
        vocab_size=tokenizer.vocab_len,
        max_seq_len=args.block_size,
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        d_ff=args.d_ff
    )
    
    print(f'Starting training for {args.epochs} epochs...')
    train_losses, val_losses = train(
        model, dataset, None,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
    
    os.makedirs('checkpoints', exist_ok=True)
    with open('checkpoints/model.pkl', 'wb') as f:
        pickle.dump({'model': model, 'tokenizer': tokenizer}, f)
    print('Model saved to checkpoints/model.pkl')
    
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='train loss')
    if val_losses:
        plt.plot(val_losses, label='val loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig('training_curve.png')
    print('Training curve saved to training_curve.png')

if __name__ == '__main__':
    main()