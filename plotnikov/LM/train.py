import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path
from bpe_tokenizer import BPETokenizer
from utils import load_corpus, create_dataset, train_val_split, batch_generator
from transformer_lm import TransformerLM, cross_entropy_loss
from constants import (
    N_LAYERS, N_HEADS, D_MODEL, D_FF, MAX_SEQ_LEN,
    BATCH_SIZE, LEARNING_RATE, BETA1, BETA2, EPSILON, NUM_EPOCHS, WARMUP_STEPS
)


def train():
    np.random.seed(42)
    
    corpus_path = "data.txt"
    tokenizer_path = "tokenizer.json"
    
    if Path(tokenizer_path).exists():
        print("Loading existing tokenizer...")
        tokenizer = BPETokenizer()
        tokenizer.load(tokenizer_path)
    else:
        print("Training BPE tokenizer...")
        corpus = load_corpus(corpus_path)
        tokenizer = BPETokenizer()
        tokenizer.train(corpus, num_merges=5000, verbose=True)
        tokenizer.save(tokenizer_path)
        print(f"Tokenizer saved to {tokenizer_path}")
    
    vocab_size = tokenizer.get_vocab_size()
    print(f"Vocabulary size: {vocab_size}")
    
    print("Creating dataset...")
    corpus = load_corpus(corpus_path)
    x, y = create_dataset(tokenizer, corpus, MAX_SEQ_LEN)
    x_train, y_train, x_val, y_val = train_val_split(x, y, val_ratio=0.1)
    
    print(f"Train samples: {len(x_train)}, Val samples: {len(x_val)}")
    
    model = TransformerLM(vocab_size, N_LAYERS, N_HEADS, D_MODEL, D_FF, MAX_SEQ_LEN)
    
    optimizer_state = {}
    for name, param, grad in model.parameters():
        optimizer_state[name] = {
            'm': np.zeros_like(param),
            'v': np.zeros_like(param),
            't': 0
        }
    
    train_losses = []
    val_losses = []
    
    print("\nStarting training...")
    for epoch in range(NUM_EPOCHS):
        epoch_loss = 0
        num_batches = 0
        
        for x_batch, y_batch in batch_generator(x_train, y_train, BATCH_SIZE):
            logits = model.forward(x_batch, training=True)
            loss, grad_logits = cross_entropy_loss(logits, y_batch)
            
            model.backward(grad_logits)
            
            lr = LEARNING_RATE * min(1.0, (epoch * len(x_train) // BATCH_SIZE + num_batches + 1) / WARMUP_STEPS)
            
            for name, param, grad in model.parameters():
                opt = optimizer_state[name]
                opt['t'] += 1
                opt['m'] = BETA1 * opt['m'] + (1 - BETA1) * grad
                opt['v'] = BETA2 * opt['v'] + (1 - BETA2) * (grad ** 2)
                m_hat = opt['m'] / (1 - BETA1 ** opt['t'])
                v_hat = opt['v'] / (1 - BETA2 ** opt['t'])
                param -= lr * m_hat / (np.sqrt(v_hat) + EPSILON)
            
            epoch_loss += loss
            num_batches += 1
        
        avg_train_loss = epoch_loss / num_batches
        train_losses.append(avg_train_loss)
        
        val_loss = 0
        val_batches = 0
        for i in range(0, len(x_val), BATCH_SIZE):
            x_batch = x_val[i:i+BATCH_SIZE]
            y_batch = y_val[i:i+BATCH_SIZE]
            
            logits = model.forward(x_batch, training=False)
            loss, _ = cross_entropy_loss(logits, y_batch)
            
            val_loss += loss
            val_batches += 1
        
        avg_val_loss = val_loss / val_batches
        val_losses.append(avg_val_loss)
        
        print(f"Epoch {epoch+1}/{NUM_EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | LR: {lr:.6f}")
    
    model_path = "model_weights.npz"
    np.savez(model_path,
             token_embedding=model.token_embedding,
             pos_embedding=model.pos_embedding,
             output_proj=model.output_proj,
             ln_final_gamma=model.ln_final.gamma,
             ln_final_beta=model.ln_final.beta)
    print(f"\nModel saved to {model_path}")
    
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Progress')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('training_curve.png', dpi=150)
    print("Training curve saved to training_curve.png")
    plt.show()
    
    with open('training_results.json', 'w') as f:
        json.dump({
            'train_losses': train_losses,
            'val_losses': val_losses,
            'hyperparameters': {
                'n_layers': N_LAYERS,
                'n_heads': N_HEADS,
                'd_model': D_MODEL,
                'd_ff': D_FF,
                'max_seq_len': MAX_SEQ_LEN,
                'batch_size': BATCH_SIZE,
                'learning_rate': LEARNING_RATE,
                'num_epochs': NUM_EPOCHS
            }
        }, f, indent=2)
    
    print("\nTraining completed successfully!")


if __name__ == "__main__":
    train()