# train.py
import torch
import torch.nn as nn
import numpy as np
import os
import time
from tqdm import tqdm
import pickle

from config import get_args
from model import TransformerLM
from data import load_data, create_dataloaders
from utils import compute_perplexity, save_checkpoint, plot_metrics


def train_epoch(model, train_loader, optimizer, criterion, device, grad_clip):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    n_batches = 0

    for batch_idx, (x, y) in enumerate(train_loader):
        x, y = x.to(device), y.to(device)

        # Forward pass
        logits = model(x)
        loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

        if batch_idx % 50 == 0:
            print(f"  Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}")

    return total_loss / n_batches


def evaluate(model, val_loader, criterion, device):
    """Evaluate model on validation set"""
    model.eval()
    total_loss = 0
    n_batches = 0

    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)

            logits = model(x)
            loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))

            total_loss += loss.item()
            n_batches += 1

    avg_loss = total_loss / n_batches
    perplexity = np.exp(avg_loss)

    return avg_loss, perplexity


def main():
    args = get_args()

    # Set device
    if args.device == 'cuda' and not torch.cuda.is_available():
        print("⚠️  CUDA не доступна, использую CPU")
        args.device = 'cpu'

    device = torch.device(args.device)
    print(f"Using device: {device}")

    # Set random seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data
    print("\n" + "=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    train_tokens, val_tokens, tokenizer = load_data(
        args.data_path, args.tokenizer_path, train_split=0.9
    )

    train_loader, val_loader = create_dataloaders(
        train_tokens, val_tokens, args.max_seq_len,
        args.batch_size, args.device
    )

    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")

    # Create model
    print("\n" + "=" * 60)
    print("CREATING MODEL")
    print("=" * 60)

    model = TransformerLM(
        vocab_size=tokenizer.vocab_size,
        d_model=args.d_model,
        n_head=args.n_head,
        n_layer=args.n_layer,
        max_seq_len=args.max_seq_len,
        dropout=args.dropout
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        betas=(args.beta1, args.beta2),
        weight_decay=args.weight_decay
    )

    # Loss function
    criterion = nn.CrossEntropyLoss()

    # Training loop
    print("\n" + "=" * 60)
    print("TRAINING")
    print("=" * 60)

    train_losses = []
    val_losses = []
    val_perplexities = []

    best_val_loss = float('inf')

    for step in range(args.max_iters):
        # Train one batch
        try:
            x, y = next(iter(train_loader))
        except StopIteration:
            # Recreate iterator
            train_loader, _ = create_dataloaders(
                train_tokens, val_tokens, args.max_seq_len,
                args.batch_size, args.device
            )
            x, y = next(iter(train_loader))

        x, y = x.to(device), y.to(device)

        # Forward
        logits = model(x)
        loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))

        # Backward
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)

        optimizer.step()

        train_losses.append(loss.item())

        # Evaluation
        if step % args.eval_interval == 0:
            val_loss, val_perplexity = evaluate(model, val_loader, criterion, device)
            val_losses.append(val_loss)
            val_perplexities.append(val_perplexity)

            print(f"\nStep {step}/{args.max_iters}")
            print(f"  Train Loss: {loss.item():.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val Perplexity: {val_perplexity:.2f}")

            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                checkpoint = {
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'step': step,
                    'loss': val_loss,
                    'perplexity': val_perplexity,
                    'config': vars(args)
                }

                os.makedirs('checkpoints', exist_ok=True)
                torch.save(checkpoint, 'checkpoints/best_model.pt')
                print(f"  ✅ Best model saved (perplexity: {val_perplexity:.2f})")

        # Save checkpoint
        if step % args.save_interval == 0 and step > 0:
            checkpoint = {
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'step': step,
                'loss': loss.item(),
                'config': vars(args)
            }
            torch.save(checkpoint, f'checkpoints/checkpoint_{step:06d}.pt')
            print(f"  💾 Checkpoint saved at step {step}")

        if step % 100 == 0:
            print(f"Step {step}, Loss: {loss.item():.4f}")

    # Plot metrics
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)

    plot_metrics(train_losses, val_losses, val_perplexities)

    # Save training history
    history = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'val_perplexities': val_perplexities
    }
    with open('training_history.pkl', 'wb') as f:
        pickle.dump(history, f)

    print(f"\nBest validation perplexity: {min(val_perplexities):.2f}")
    print("Training completed!")


if __name__ == "__main__":
    main()