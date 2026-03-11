import numpy as np
import json
import matplotlib.pyplot as plt
from tqdm import tqdm
from tokenizer import BPETokenizer, get_or_create_data
from model import TransformerLM
from optim import Adam

CONFIG = {
    "n_layer": 2,
    "n_head": 4,
    "d_model": 128,
    "d_ff": 512,
    "max_seq_len": 64,
    "batch_size": 16,
    "epochs": 10,
    "lr": 1e-4,
    "vocab_size": 512
}

def load_data(path="data.txt"):
    text = get_or_create_data(path)
    return text

def create_batches(data_ids, seq_len, batch_size):
    n_batches = len(data_ids) // (seq_len * batch_size)
    X = []
    Y = []
    for i in range(n_batches):
        start = i * seq_len * batch_size
        batch_data = np.array(data_ids[start : start + seq_len * batch_size])
        batch_data = batch_data.reshape(batch_size, seq_len)
        
        x = batch_data[:, :-1]
        y = batch_data[:, 1:]
        
        if x.shape[1] < seq_len - 1: 
            continue
            
        X.append(x)
        Y.append(y)
    return X, Y

def cross_entropy_loss(logits, targets):
    B, T, V = logits.shape
    
    logits_max = np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits - logits_max)
    probs = exp_logits / (np.sum(exp_logits, axis=-1, keepdims=True) + 1e-9)
    
    targets_exp = targets.reshape(B, T, 1)
    p_t = np.take_along_axis(probs, targets_exp, axis=-1).squeeze(-1)
    
    loss = -np.mean(np.log(p_t + 1e-9))
    
    dlogits = probs.copy()
    one_hot = np.zeros_like(probs)
    np.put_along_axis(one_hot, targets_exp, 1, axis=-1)
    dlogits -= one_hot
    dlogits /= (B * T)
    
    return loss, dlogits

def main():
    print("Loading data...")
    text = load_data()
    
    print("Training Tokenizer...")
    tokenizer = BPETokenizer(vocab_size=CONFIG["vocab_size"])
    tokenizer.train(text)
    tokenizer.save("tokenizer.json")
    
    data_ids = tokenizer.encode(text)
    print(f"Vocab size: {tokenizer.vocab_size}, Data len: {len(data_ids)}")
    
    CONFIG["vocab_size"] = tokenizer.vocab_size
    
    X_batch, Y_batch = create_batches(data_ids, CONFIG["max_seq_len"], CONFIG["batch_size"])
    print(f"Number of batches: {len(X_batch)}")
    
    print("Initializing Model...")
    np.random.seed(42)
    model = TransformerLM(
        vocab_size=CONFIG["vocab_size"],
        d_model=CONFIG["d_model"],
        n_head=CONFIG["n_head"],
        n_layer=CONFIG["n_layer"],
        max_seq_len=CONFIG["max_seq_len"],
        d_ff=CONFIG["d_ff"]
    )
    
    optimizer = Adam(model, lr=CONFIG["lr"])
    
    train_losses = []
    
    print("Starting Training...")
    for epoch in range(CONFIG["epochs"]):
        epoch_loss = 0.0
        pbar = tqdm(range(len(X_batch)), desc=f"Epoch {epoch+1}")
        
        for i in pbar:
            x = X_batch[i]
            y = Y_batch[i]
            
            logits = model.forward(x)
            loss, dlogits = cross_entropy_loss(logits, y)
            
            model.zero_grad()
            model.backward(dlogits)
            optimizer.step()
            
            epoch_loss += loss
            pbar.set_postfix({"loss": f"{loss:.4f}"})
            
        avg_loss = epoch_loss / len(X_batch)
        train_losses.append(avg_loss)
        print(f"Epoch {epoch+1} finished. Avg Loss: {avg_loss:.4f}")
        
    params = {k: v.tolist() for k, v in model.params.items()}
    with open("model_weights.json", 'w') as f:
        json.dump(params, f)
        
    plt.plot(train_losses)
    plt.title("Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.savefig("loss_plot.png")
    print("Training finished. Plot saved to loss_plot.png")

if __name__ == "__main__":
    main()