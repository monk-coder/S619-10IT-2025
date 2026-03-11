import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
from bpe_tokenizer import BPETokenizer, prepare_data
from model import TransformerLM, loss_fn

# ============= ШАГ 4: Оптимизатор (вставляем сюда) =============
class AdamOptimizer:
    """Adam оптимизатор"""
    def __init__(self, learning_rate=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = []  # моменты первого порядка
        self.v = []  # моменты второго порядка
    
    def init_params(self, params: list):
        """Инициализация моментов для каждого параметра"""
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
    
    def step(self, params: list, grads: list):
        """Один шаг оптимизации"""
        self.t += 1
        
        for i, (p, g) in enumerate(zip(params, grads)):
            # Обновление моментов
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * g
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (g * g)
            
            # Коррекция смещения
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)
            
            # Обновление параметров
            p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


# ============= ШАГ 5: DataLoader и функции обучения =============
class DataLoader:
    """Загрузчик данных для обучения"""
    def __init__(self, texts: list, tokenizer, seq_len: int, batch_size: int):
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.batch_size = batch_size
        
        # Токенизируем все тексты
        print("Токенизация данных...")
        all_tokens = []
        for text in tqdm(texts):
            tokens = tokenizer.encode(text)
            if len(tokens) > 0:
                all_tokens.extend(tokens)
        
        # Создаем последовательности
        self.data = np.array(all_tokens)
        self.num_batches = (len(self.data) - 1) // (seq_len * batch_size)
        
        print(f"Всего токенов: {len(self.data)}")
        print(f"Количество батчей: {self.num_batches}")
    
    def __len__(self):
        """Возвращает количество батчей"""
        return self.num_batches
    
    def __iter__(self):
        self.i = 0
        return self
    
    def __next__(self):
        if self.i >= self.num_batches:
            raise StopIteration
        
        start = self.i * self.seq_len * self.batch_size
        end = start + self.seq_len * self.batch_size + 1
        
        batch_data = self.data[start:end]
        
        # Создаем входы и цели
        x = batch_data[:-1].reshape(self.batch_size, self.seq_len)
        y = batch_data[1:].reshape(self.batch_size, self.seq_len)
        
        self.i += 1
        return x, y


def train_epoch(model, dataloader, optimizer, epoch_num):
    """Обучение одной эпохи"""
    total_loss = 0
    
    for batch_idx, (x, y) in enumerate(tqdm(dataloader, desc=f"Epoch {epoch_num}")):
        # Forward pass
        logits = model.forward(x)
        
        # Loss
        loss, dlogits = loss_fn(logits, y)
        total_loss += loss
        
        # Backward pass
        model.backward(dlogits)
        
        # Обновление параметров
        params = model.get_parameters()
        grads = model.get_gradients()
        optimizer.step(params, grads)
        
        if batch_idx % 10 == 0:
            tqdm.write(f"Batch {batch_idx}, Loss: {loss:.4f}")
    
    return total_loss / len(dataloader)


def validate(model, val_texts, tokenizer, seq_len, num_batches=5):
    """Валидация модели с защитой от деления на ноль"""
    total_loss = 0
    count = 0
    
    # Берем только первые несколько текстов для валидации
    val_sample = val_texts[:20]  # берем 20 текстов
    
    for text in val_sample:
        try:
            # Токенизируем текст
            tokens = tokenizer.encode(text)
            if len(tokens) < seq_len + 1:
                continue  # пропускаем слишком короткие тексты
            
            # Создаем один батч
            tokens = np.array(tokens[:seq_len + 1])
            x = tokens[:-1].reshape(1, -1)
            y = tokens[1:].reshape(1, -1)
            
            # Forward pass
            logits = model.forward(x)
            loss, _ = loss_fn(logits, y)
            total_loss += loss
            count += 1
            
            if count >= num_batches:
                break
                
        except Exception as e:
            print(f"Ошибка при валидации: {e}")
            continue
    
    if count == 0:
        print("ВНИМАНИЕ: Нет данных для валидации, возвращаем loss=10.0")
        return 10.0
    
    return total_loss / count


# ============= ШАГ 6: Главная функция обучения =============
def main():
    # Гиперпараметры
    D_MODEL = 128      # Размер эмбеддингов
    N_HEAD = 4         # Количество голов attention
    N_LAYER = 3        # Количество слоев трансформера
    MAX_SEQ_LEN = 128  # Максимальная длина последовательности
    BATCH_SIZE = 32    # Размер батча
    EPOCHS = 10        # Количество эпох
    LR = 1e-3          # Learning rate
    
    print("=" * 60)
    print("ОБУЧЕНИЕ ЯЗЫКОВОЙ МОДЕЛИ TRANSFORMER")
    print("=" * 60)
    
    # 1. Загрузка токенизатора
    print("\n1. Загрузка токенизатора...")
    tokenizer = BPETokenizer()
    tokenizer.load("bpe_tokenizer.json")
    VOCAB_SIZE = len(tokenizer.vocab)
    print(f"Размер словаря: {VOCAB_SIZE}")
    
    # 2. Подготовка данных
    print("\n2. Подготовка данных...")
    train_texts, val_texts = prepare_data("data.txt", train_ratio=0.9)
    
    # 3. Создание даталоадера
    print("\n3. Создание даталоадера...")
    train_loader = DataLoader(train_texts, tokenizer, MAX_SEQ_LEN, BATCH_SIZE)
    
    # 4. Инициализация модели
    print("\n4. Инициализация модели...")
    model = TransformerLM(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN
    )
    
    # 5. Инициализация оптимизатора
    print("\n5. Инициализация оптимизатора...")
    optimizer = AdamOptimizer(learning_rate=LR)
    optimizer.init_params(model.get_parameters())
    
    # 6. Обучение
    print("\n6. Начало обучения...")
    train_losses = []
    val_losses = []
    
    for epoch in range(1, EPOCHS + 1):
        print(f"\n--- Эпоха {epoch} ---")
        
        # Обучение
        train_loss = train_epoch(model, train_loader, optimizer, epoch)
        train_losses.append(train_loss)
        
        # Валидация
        val_loss = validate(model, val_texts, tokenizer, MAX_SEQ_LEN)
        val_losses.append(val_loss)
        
        print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Сохранение модели после каждой эпохи
        with open(f"model_epoch_{epoch}.pkl", 'wb') as f:
            pickle.dump({
                'model': model,
                'train_loss': train_loss,
                'val_loss': val_loss
            }, f)
    
    # 7. Построение графика обучения
    print("\n7. Построение графика обучения...")
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Train Loss', marker='o')
    plt.plot(val_losses, label='Validation Loss', marker='s')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig('training_loss.png')
    plt.show()
    
    # 8. Сохранение финальной модели
    print("\n8. Сохранение финальной модели...")
    with open("transformer_lm_final.pkl", 'wb') as f:
        pickle.dump({
            'model': model,
            'train_losses': train_losses,
            'val_losses': val_losses
        }, f)
    print("Обучение завершено!")


if __name__ == "__main__":
    main()