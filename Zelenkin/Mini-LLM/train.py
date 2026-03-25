import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from bpe_tokenizer import BPETokenizer
from data_utils import create_dataloader
from model import TransformerLM
from optimization import Adam


def collect_parameters(model):
    """Collect all trainable parameters from the model"""
    params = []

    def collect(obj):
        if hasattr(obj, 'W') and obj.W is not None:
            params.append(obj)
        if hasattr(obj, 'b') and obj.b is not None:
            params.append(obj)
        for attr_name in dir(obj):
            if attr_name.startswith('_') or attr_name in ['cache', 'mask']:
                continue
            attr = getattr(obj, attr_name)
            if hasattr(attr, '__dict__') and not isinstance(attr, type):
                collect(attr)

    collect(model)
    return params


def main():
    """Main training function"""
    print("=" * 50)
    print("Decoder-only Transformer Language Model")
    print("=" * 50)

    # Load configuration
    config = Config()
    np.random.seed(config.seed)

    # Initialize tokenizer
    print("\n[1/4] Initializing tokenizer...")
    tokenizer = BPETokenizer()

    # Load and tokenize data
    print("[2/4] Loading and tokenizing data...")
    try:
        with open(config.data_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"Loaded {len(text)} characters")
    except FileNotFoundError:
        print(f"Error: {config.data_path} not found!")
        print("Creating sample data file...")
        text = """
        Once upon a time in a small village there lived a young programmer who loved machine learning.
        Every day they would study neural networks and transformers.
        They dreamed of creating an AI that could understand human language.
        After many months of hard work, they finally built their first language model.
        The model learned to generate text and everyone was amazed by its capabilities.
        """
        with open(config.data_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Created sample data with {len(text)} characters")

    # Train BPE
    tokenizer.train(text, num_merges=500)
    config.vocab_size = len(tokenizer.vocab)
    print(f"Vocabulary size: {config.vocab_size}")

    # Tokenize
    tokens = tokenizer.encode(text)
    print(f"Total tokens: {len(tokens)}")

    # Create dataloader
    dataloader = create_dataloader(
        tokens,
        config.block_size,
        config.batch_size,
        config.train_split
    )

    # Initialize model
    print("[3/4] Initializing model...")
    model = TransformerLM(config)
    print(f"Model parameters:")
    print(f"  - d_model: {config.d_model}")
    print(f"  - n_head: {config.n_head}")
    print(f"  - n_layer: {config.n_layer}")
    print(f"  - block_size: {config.block_size}")
    print(f"  - vocab_size: {config.vocab_size}")

    # Collect parameters for optimizer
    params = collect_parameters(model)
    print(f"  - Trainable parameters: {len(params)} layers")

    # Initialize optimizer
    optimizer = Adam(params, lr=config.learning_rate)

    # Training loop
    print("[4/4] Starting training...")
    train_losses = []
    val_losses = []
    val_epochs = []

    start_time = time.time()

    # Calculate number of batches
    if len(dataloader.train_tokens) > config.block_size * config.batch_size:
        n_batches = min(100, len(dataloader.train_tokens) // (config.block_size * config.batch_size))
    else:
        n_batches = 10

    n_val_batches = max(1, min(20, len(dataloader.val_tokens) // (config.block_size * config.batch_size))) if len(
        dataloader.val_tokens) > config.block_size else 1

    for epoch in range(config.n_epochs):
        # Training
        epoch_losses = []

        for batch_idx in tqdm(range(n_batches), desc=f"Epoch {epoch + 1}/{config.n_epochs}"):
            try:
                x, y = dataloader.get_batch('train')

                # Forward pass
                logits = model.forward(x)
                loss, dlogits = model.compute_loss(logits, y)
                epoch_losses.append(loss)

                # Backward pass
                model.backward(dlogits)

                # Update parameters
                optimizer.step()
            except Exception as e:
                print(f"Error in batch {batch_idx}: {e}")
                continue

        if epoch_losses:
            train_loss = np.mean(epoch_losses)
            train_losses.append(train_loss)
        else:
            train_loss = 0
            train_losses.append(0)

        # Validation
        if (epoch + 1) % config.eval_interval == 0 and n_val_batches > 0:
            val_epoch_losses = []

            for batch_idx in range(n_val_batches):
                try:
                    x_val, y_val = dataloader.get_batch('val')
                    logits_val = model.forward(x_val)
                    loss_val, _ = model.compute_loss(logits_val, y_val)
                    val_epoch_losses.append(loss_val)
                except Exception as e:
                    continue

            if val_epoch_losses:
                val_loss = np.mean(val_epoch_losses)
                val_losses.append(val_loss)
                val_epochs.append(epoch + 1)
                print(f"\nEpoch {epoch + 1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
            else:
                print(f"\nEpoch {epoch + 1}: train_loss={train_loss:.4f}")
        else:
            print(f"\nEpoch {epoch + 1}: train_loss={train_loss:.4f}")

    elapsed_time = time.time() - start_time
    print(f"\nTraining completed in {elapsed_time / 60:.2f} minutes")

    # Save model
    print("Saving model...")
    try:
        model_params = {
            'token_embedding': model.token_embedding.W,
            'pos_embedding': model.pos_embedding.W,
            'lm_head': model.lm_head.W,
            'lm_head_bias': model.lm_head.b
        }
        np.savez('model_params.npz', **model_params)
        print("Model saved to model_params.npz")
    except Exception as e:
        print(f"Error saving model: {e}")

    # Plot training curve
    if train_losses:
        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.plot(train_losses, label='Train Loss', linewidth=2)
        if val_losses:
            plt.plot(val_epochs, val_losses, label='Val Loss', marker='o', markersize=4)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training Progress')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.subplot(1, 2, 2)
        recent = min(20, len(train_losses))
        plt.plot(range(len(train_losses) - recent, len(train_losses)), train_losses[-recent:],
                 label='Recent Train Loss', linewidth=2, color='orange')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Recent Training Progress')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('training_plot.png', dpi=100)
        plt.show()

        print("\nTraining plot saved to training_plot.png")
    else:
        print("\nNo training data to plot")

    return model, tokenizer


if __name__ == "__main__":
    try:
        model, tokenizer = main()
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback

        traceback.print_exc()