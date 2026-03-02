import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from model import TransformerLM, loss_fn
from optimizer import Adam

def get_batches(data, batch_size, seq_len):
    """Генерирует батчи из данных"""
    n_batches = len(data) // (batch_size * seq_len)
    data = data[:n_batches * batch_size * seq_len]
    data = data.reshape(batch_size, -1)
    
    for i in range(0, data.shape[1] - seq_len, seq_len):
        x = data[:, i:i+seq_len]
        y = data[:, i+1:i+seq_len+1]
        yield x, y

def train(model, train_data, val_data, epochs, batch_size, seq_len, lr=0.001):
    optimizer = Adam(model.get_parameters(), lr=lr)
    
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        # Training
        model.train()
        epoch_loss = 0
        n_batches = 0
        
        for x, y in tqdm(get_batches(train_data, batch_size, seq_len), desc=f'Epoch {epoch+1}'):
            optimizer.zero_grad()
            
            # Forward
            logits = model.forward(x)
            loss, dlogits = loss_fn(logits, y)
            
            # Backward
            model.backward(dlogits)
            
            # Update
            optimizer.step()
            
            epoch_loss += loss
            n_batches += 1
        
        avg_train_loss = epoch_loss / n_batches
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        n_val_batches = 0
        
        for x, y in get_batches(val_data, batch_size, seq_len):
            logits = model.forward(x)
            loss, _ = loss_fn(logits, y)
            val_loss += loss
            n_val_batches += 1
        
        avg_val_loss = val_loss / n_val_batches
        val_losses.append(avg_val_loss)
        
        print(f'Epoch {epoch+1}: train loss = {avg_train_loss:.4f}, val loss = {avg_val_loss:.4f}')
    
    # Plot losses
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train')
    plt.plot(val_losses, label='Validation')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig('training_loss.png')
    plt.show()
    
    return train_losses, val_losses

if __name__ == '__main__':
    # Загружаем данные и токенизатор из задания 3
    from bpe import BPETokenizer  # ваш токенизатор
    
    # Гиперпараметры (небольшие для быстрого обучения)
    VOCAB_SIZE = 1000  # размер словаря BPE
    D_MODEL = 128
    N_HEAD = 4
    N_LAYER = 3
    MAX_SEQ_LEN = 128
    BATCH_SIZE = 32
    EPOCHS = 10
    LR = 0.001
    
    # Инициализация
    tokenizer = BPETokenizer()
    tokenizer.load('bpe_model.json')  # загружаем обученный BPE
    
    # Загружаем и токенизируем данные
    with open('data.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    tokens = tokenizer.encode(text)
    data = np.array(tokens)
    
    # Разделяем на train/val
    split = int(0.9 * len(data))
    train_data = data[:split]
    val_data = data[split:]
    
    # Создаем модель
    model = TransformerLM(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN
    )
    
    # Обучаем
    train_losses, val_losses = train(
        model, train_data, val_data,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        seq_len=MAX_SEQ_LEN,
        lr=LR
    )
    
    # Сохраняем модель
    import pickle
    with open('model_params.pkl', 'wb') as f:
        params = [p for p, _ in model.get_parameters()]
        pickle.dump(params, f)
