#!/usr/bin/env python3
import argparse, os, json, time
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

from data import load_data, TokenDataset, get_dataloader, train_tokenizer, load_tokenizer
from transformer import TransformerLM
from optim import Adam
from utils import cross_entropy_loss, cross_entropy_backward


def train(model: TransformerLM, train_ds, val_ds, args):
    opt = Adam(model.params(), lr=args.lr)
    history = {'train_loss': [], 'val_loss': [], 'time': []}
    
    for epoch in range(args.epochs):
        model_train_loss = 0
        n_batches = 0
        start = time.time()
        
        for xb, yb in tqdm(get_dataloader(train_ds, args.batch_size), desc=f'Epoch {epoch+1}'):
            logits = model.forward(xb, training=True)
            loss, probs = cross_entropy_loss(logits, yb)
            grad = cross_entropy_backward(probs, yb)
            grads = model.backward(grad)
            opt.step(model.params(), grads)
            model_train_loss += loss
            n_batches += 1
        
        val_loss = 0
        n_val = 0
        for xb, yb in get_dataloader(val_ds, args.batch_size, shuffle=False):
            logits = model.forward(xb, training=False)
            loss, _ = cross_entropy_loss(logits, yb)
            val_loss += loss * len(xb)
            n_val += len(xb)
        val_loss /= max(1, n_val)
        
        avg_train_loss = model_train_loss / max(1, n_batches)
        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(val_loss)
        history['time'].append(time.time() - start)
        print(f"Epoch {epoch+1}: train={avg_train_loss:.4f}, val={val_loss:.4f}, t={history['time'][-1]:.1f}s")
        
        if (epoch + 1) % args.save_every == 0:
            np.savez(os.path.join(args.out_dir, f'ckpt_ep{epoch+1}.npz'), **model.params())
            with open(os.path.join(args.out_dir, 'history.json'), 'w') as f:
                json.dump(history, f)
    
    plt.figure()
    plt.plot(history['train_loss'], label='train')
    plt.plot(history['val_loss'], label='val')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()
    plt.savefig(os.path.join(args.out_dir, 'loss.png'))
    plt.close()
    return history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='data.txt')
    parser.add_argument('--out_dir', type=str, default='out')
    parser.add_argument('--seq_len', type=int, default=128)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--d_model', type=int, default=128)
    parser.add_argument('--n_layer', type=int, default=2)
    parser.add_argument('--n_head', type=int, default=2)
    parser.add_argument('--d_ff', type=int, default=256)
    parser.add_argument('--save_every', type=int, default=5)
    parser.add_argument('--vocab_size', type=int, default=1000)
    parser.add_argument('--tokenizer_path', type=str, default='tokenizer.json')
    parser.add_argument('--force_retrain', action='store_true', help='Force retrain tokenizer')
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    print("Loading data...")
    text = load_data(args.data)
    
    # Force retrain if requested
    if args.force_retrain and os.path.exists(args.tokenizer_path):
        print(f"Removing old tokenizer: {args.tokenizer_path}")
        os.remove(args.tokenizer_path)
    
    if os.path.exists(args.tokenizer_path):
        print(f"Loading tokenizer from {args.tokenizer_path}")
        tokenizer = load_tokenizer(args.tokenizer_path)
    else:
        print("Training new tokenizer...")
        tokenizer = train_tokenizer(text, args.vocab_size, args.tokenizer_path)
    
    print(f"'\\n' in vocab: {'\\n' in tokenizer.token2id}")
    print(f"Vocab size: {len(tokenizer)}")
    
    print("Tokenizing data...")
    all_tokens = np.array(tokenizer.encode(text), dtype=np.int32)
    print(f"Total tokens: {len(all_tokens)}")
    
    split = int(len(all_tokens) * 0.9)
    train_tokens = all_tokens[:split]
    val_tokens = all_tokens[split:]
    
    train_ds = TokenDataset(train_tokens, args.seq_len)
    val_ds = TokenDataset(val_tokens, args.seq_len)
    
    print(f"Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")
    
    model = TransformerLM(
        vocab_size=len(tokenizer),
        max_seq_len=args.seq_len,
        d_model=args.d_model,
        n_layer=args.n_layer,
        n_head=args.n_head,
        d_ff=args.d_ff,
        dropout=0.1
    )
    
    print(f"Model params: {sum(p.size for p in model.params().values()):,}")
    train(model, train_ds, val_ds, args)


if __name__ == '__main__':
    main()