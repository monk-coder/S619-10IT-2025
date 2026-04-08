import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from core import TransformerLM
from bpe_tokenizer import BPETokenizer
import pickle


def load_data(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            return text[:200000]  # Use 200k chars for faster training
    except:
        sample_text = "The quick brown fox jumps over the lazy dog. " * 1000
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        return sample_text


def get_batches(tokens, seq_len, batch_size):
    """Generate batches of data"""
    n_samples = (len(tokens) - seq_len) // seq_len
    if n_samples <= 0:
        return None, None

    X = []
    Y = []
    for i in range(0, n_samples * seq_len, seq_len):
        if i + seq_len + 1 > len(tokens):
            break
        X.append(tokens[i:i + seq_len])
        Y.append(tokens[i + 1:i + seq_len + 1])

    X = np.array(X)
    Y = np.array(Y)

    n_batches = len(X) // batch_size
    if n_batches == 0:
        return X.reshape(1, len(X), seq_len), Y.reshape(1, len(Y), seq_len)

    X = X[:n_batches * batch_size].reshape(n_batches, batch_size, seq_len)
    Y = Y[:n_batches * batch_size].reshape(n_batches, batch_size, seq_len)

    return X, Y


def cross_entropy_loss(logits, targets):
    """Compute cross entropy loss and gradient"""
    batch_size, seq_len, vocab_size = logits.shape

    logits_flat = logits.reshape(-1, vocab_size)
    targets_flat = targets.reshape(-1)

    # Softmax with numerical stability
    max_logits = np.max(logits_flat, axis=1, keepdims=True)
    exp_logits = np.exp(logits_flat - max_logits)
    probs = exp_logits / (np.sum(exp_logits, axis=1, keepdims=True) + 1e-8)

    # Loss
    loss = -np.mean(np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-8))

    # Gradient
    dlogits = probs.copy()
    dlogits[np.arange(len(targets_flat)), targets_flat] -= 1
    dlogits = dlogits.reshape(batch_size, seq_len, vocab_size) / (batch_size * seq_len)

    return loss, dlogits


def update_model(model, learning_rate):
    """SGD update for all parameters"""
    # Update embeddings
    model.token_embedding -= learning_rate * model.d_token_embedding
    model.pos_embedding -= learning_rate * model.d_pos_embedding

    # Update transformer blocks
    for block in model.blocks:
        block.ln1.gamma -= learning_rate * block.ln1.dgamma
        block.ln1.beta -= learning_rate * block.ln1.dbeta

        block.attn.W_q.W -= learning_rate * block.attn.W_q.dW
        block.attn.W_q.b -= learning_rate * block.attn.W_q.db
        block.attn.W_k.W -= learning_rate * block.attn.W_k.dW
        block.attn.W_k.b -= learning_rate * block.attn.W_k.db
        block.attn.W_v.W -= learning_rate * block.attn.W_v.dW
        block.attn.W_v.b -= learning_rate * block.attn.W_v.db
        block.attn.W_o.W -= learning_rate * block.attn.W_o.dW
        block.attn.W_o.b -= learning_rate * block.attn.W_o.db

        block.ln2.gamma -= learning_rate * block.ln2.dgamma
        block.ln2.beta -= learning_rate * block.ln2.dbeta

        block.mlp.fc1.W -= learning_rate * block.mlp.fc1.dW
        block.mlp.fc1.b -= learning_rate * block.mlp.fc1.db
        block.mlp.fc2.W -= learning_rate * block.mlp.fc2.dW
        block.mlp.fc2.b -= learning_rate * block.mlp.fc2.db

    # Final layer
    model.ln_final.gamma -= learning_rate * model.ln_final.dgamma
    model.ln_final.beta -= learning_rate * model.ln_final.dbeta
    model.lm_head.W -= learning_rate * model.lm_head.dW
    model.lm_head.b -= learning_rate * model.lm_head.db


def train():
    # Hyperparameters
    d_model = 128  # Increased for better learning
    n_layer = 3  # Increased
    n_head = 4  # Increased
    max_seq_len = 64  # Increased
    batch_size = 16  # Increased
    learning_rate = 0.003
    n_epochs = 10

    print("Loading data...")
    text = load_data('data.txt')
    print(f"Loaded {len(text)} characters")

    print("Initializing tokenizer...")
    tokenizer = BPETokenizer()
    vocab_size = tokenizer.train(text, vocab_size=300)

    with open('tokenizer.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)

    print("Tokenizing text...")
    tokens = tokenizer.encode(text)
    print(f"Total tokens: {len(tokens)}")

    # Train/val split
    split_idx = int(0.9 * len(tokens))
    train_tokens = tokens[:split_idx]
    val_tokens = tokens[split_idx:]

    print("Creating batches...")
    train_x, train_y = get_batches(train_tokens, max_seq_len, batch_size)
    val_x, val_y = get_batches(val_tokens, max_seq_len, batch_size)

    if train_x is None or len(train_x) == 0:
        print("Not enough data")
        return

    print(f"Train batches: {train_x.shape[0]}, Val batches: {val_x.shape[0]}")

    print("Initializing model...")
    model = TransformerLM(vocab_size, d_model, n_layer, n_head, max_seq_len)

    train_losses = []
    val_losses = []

    for epoch in range(n_epochs):
        total_train_loss = 0
        n_batches = min(train_x.shape[0], 1000)

        for i in tqdm(range(n_batches), desc=f"Epoch {epoch + 1}/{n_epochs}"):
            x_batch = train_x[i]
            y_batch = train_y[i]

            # Store input tokens for gradient computation
            model.cache = {'input_tokens': x_batch}

            # Forward pass
            logits = model.forward(x_batch)
            loss, dlogits = cross_entropy_loss(logits, y_batch)
            total_train_loss += loss

            # Backward pass with input tokens
            dout = model.lm_head.backward(dlogits)
            dout = model.ln_final.backward(dout)

            for block in reversed(model.blocks):
                dout = block.backward(dout)

            # Gradient for embeddings
            model.d_token_embedding = np.zeros_like(model.token_embedding)
            for b in range(dout.shape[0]):
                for t in range(dout.shape[1]):
                    token_id = x_batch[b, t]
                    model.d_token_embedding[token_id] += dout[b, t]

            model.d_pos_embedding = np.zeros_like(model.pos_embedding)
            seq_len = dout.shape[1]
            model.d_pos_embedding[:seq_len] = np.sum(dout, axis=(0, 1))

            # Update parameters
            update_model(model, learning_rate)

        avg_train_loss = total_train_loss / n_batches
        train_losses.append(avg_train_loss)

        # Validation
        total_val_loss = 0
        for i in range(min(val_x.shape[0], 100)):
            x_batch = val_x[i]
            y_batch = val_y[i]
            logits = model.forward(x_batch)
            loss, _ = cross_entropy_loss(logits, y_batch)
            total_val_loss += loss

        avg_val_loss = total_val_loss / min(val_x.shape[0], 100)
        val_losses.append(avg_val_loss)

        print(f"Epoch {epoch + 1}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")

        # Test generation every 2 epochs
        if (epoch + 1) % 2 == 0:
            test_prompt = "The "
            test_tokens = tokenizer.encode(test_prompt)
            for _ in range(30):
                x = np.array([test_tokens[-max_seq_len:]])
                logits = model.forward(x)
                probs = np.exp(logits[0, -1, :]) / np.sum(np.exp(logits[0, -1, :]))
                next_token = np.random.choice(len(probs), p=probs)
                test_tokens.append(next_token)
            generated = tokenizer.decode(test_tokens)
            print(f"Sample: {generated[:100]}...")

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Train Loss', marker='o')
    plt.plot(val_losses, label='Val Loss', marker='o')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Curves')
    plt.legend()
    plt.grid(True)
    plt.savefig('training_curves.png')
    print("Training curves saved to 'training_curves.png'")

    model_params = {
        'token_embedding': model.token_embedding,
        'pos_embedding': model.pos_embedding,
        'd_model': d_model,
        'n_layer': n_layer,
        'n_head': n_head,
        'max_seq_len': max_seq_len
    }
    np.save('model_final.npy', model_params)
    print("Model saved to model_final.npy!")


if __name__ == "__main__":
    train()