import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
import os
from bpe_tokenizer import BPETokenizer, prepare_data
from model import TransformerLM, loss_and_accuracy


class AdamOptimizer:
    """Adam оптимизатор с learning rate scheduling"""
    def __init__(self, learning_rate=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, warmup_steps=1000):
        self.base_lr = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.warmup_steps = warmup_steps
        self.t = 0
        self.m = []
        self.v = []
    
    def init_params(self, params: list):
        """Инициализация моментов для каждого параметра"""
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
    
    def get_lr(self):
        """Получение текущего learning rate с warmup"""
        self.t += 1
        if self.t < self.warmup_steps:
            return self.base_lr * (self.t / self.warmup_steps)
        else:
            # Косинусное затухание
            progress = (self.t - self.warmup_steps) / (10000 - self.warmup_steps)
            return self.base_lr * 0.5 * (1 + np.cos(np.pi * progress))
    
    def step(self, params: list, grads: list):
        """Один шаг оптимизации"""
        lr = self.get_lr()
        
        for i, (p, g) in enumerate(zip(params, grads)):
            # Обновление моментов
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * g
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (g * g)
            
            # Коррекция смещения
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)
            
            # Обновление параметров
            p -= lr * m_hat / (np.sqrt(v_hat) + self.eps)


class DataLoader:
    """Загрузчик данных для обучения"""
    def __init__(self, texts: list, tokenizer, seq_len: int, batch_size: int, shuffle: bool = True):
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        # Токенизируем все тексты
        print("Токенизация данных...")
        all_tokens = []
        for text in tqdm(texts, desc="Tokenizing"):
            tokens = tokenizer.encode(text)
            if len(tokens) > 0:
                all_tokens.extend(tokens)
        
        # Создаем последовательности
        self.data = np.array(all_tokens)
        
        # Обрезаем до кратного размера
        total_len = (len(self.data) - 1) // (seq_len * batch_size) * (seq_len * batch_size)
        self.data = self.data[:total_len + 1]
        
        self.num_batches = (len(self.data) - 1) // (seq_len * batch_size)
        
        print(f"Всего токенов: {len(self.data)}")
        print(f"Количество батчей: {self.num_batches}")
    
    def __len__(self):
        return self.num_batches
    
    def __iter__(self):
        self.i = 0
        if self.shuffle:
            # Перемешиваем данные
            indices = np.random.permutation(len(self.data) - self.seq_len * self.batch_size)
            self.data = self.data[indices]
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
    model.train()
    total_loss = 0
    total_accuracy = 0
    num_batches = 0
    
    pbar = tqdm(dataloader, desc=f"Epoch {epoch_num}")
    for batch_idx, (x, y) in enumerate(pbar):
        # Forward pass
        logits = model.forward(x)
        
        # Loss и accuracy
        loss, dlogits, accuracy = loss_and_accuracy(logits, y)
        total_loss += loss
        total_accuracy += accuracy
        num_batches += 1
        
        # Backward pass
        model.backward(dlogits)
        
        # Обновление параметров
        params = model.get_parameters()
        grads = model.get_gradients()
        optimizer.step(params, grads)
        model.zero_grad()
        
        # Обновление прогресс-бара
        pbar.set_postfix({
            'loss': f'{loss:.4f}',
            'acc': f'{accuracy:.2%}',
            'lr': f'{optimizer.get_lr():.2e}'
        })
    
    return total_loss / num_batches, total_accuracy / num_batches


def validate(model, val_texts, tokenizer, seq_len, num_batches=20):
    """Валидация модели"""
    model.eval()
    total_loss = 0
    total_accuracy = 0
    count = 0
    
    # Случайно выбираем тексты для валидации
    indices = np.random.permutation(len(val_texts))[:num_batches * 2]
    
    for idx in indices:
        try:
            text = val_texts[idx]
            tokens = tokenizer.encode(text)
            
            if len(tokens) < seq_len + 1:
                continue
            
            # Берем несколько срезов из длинного текста
            num_slices = min(3, (len(tokens) - seq_len) // (seq_len // 2))
            
            for s in range(num_slices):
                start = s * (seq_len // 2)
                end = start + seq_len + 1
                
                if end > len(tokens):
                    continue
                
                slice_tokens = np.array(tokens[start:end])
                x = slice_tokens[:-1].reshape(1, -1)
                y = slice_tokens[1:].reshape(1, -1)
                
                logits = model.forward(x)
                loss, _, accuracy = loss_and_accuracy(logits, y)
                
                total_loss += loss
                total_accuracy += accuracy
                count += 1
                
                if count >= num_batches:
                    break
            
            if count >= num_batches:
                break
                
        except Exception as e:
            print(f"Ошибка при валидации: {e}")
            continue
    
    if count == 0:
        return 10.0, 0.0
    
    return total_loss / count, total_accuracy / count


def generate_text(model, tokenizer, prompt, max_length=50, temperature=0.8):
    """Генерация текста"""
    model.eval()
    
    # Токенизируем промпт
    tokens = tokenizer.encode(prompt)
    input_ids = np.array(tokens).reshape(1, -1)
    
    generated = tokens.copy()
    
    for _ in range(max_length):
        # Обрезаем до максимальной длины
        if input_ids.shape[1] > model.max_seq_len:
            input_ids = input_ids[:, -model.max_seq_len:]
        
        # Получаем предсказания
        logits = model.forward(input_ids)
        
        # Берем логиты последнего токена
        next_token_logits = logits[0, -1, :]
        
        # Применяем температуру
        next_token_logits = next_token_logits / temperature
        
        # Softmax для вероятностей
        exp_logits = np.exp(next_token_logits - np.max(next_token_logits))
        probs = exp_logits / np.sum(exp_logits)
        
        # Сэмплируем следующий токен
        next_token = np.random.choice(len(probs), p=probs)
        
        # Добавляем к сгенерированному
        generated.append(next_token)
        input_ids = np.array([generated]).reshape(1, -1)
    
    # Декодируем обратно в текст
    return tokenizer.decode(generated)


def main():
    # Гиперпараметры
    D_MODEL = 256      # Увеличили с 128 до 256
    N_HEAD = 8         # Увеличили с 4 до 8
    N_LAYER = 6        # Увеличили с 3 до 6
    MAX_SEQ_LEN = 128  # Максимальная длина последовательности
    BATCH_SIZE = 16    # Уменьшили с 32 до 16 из-за большей модели
    EPOCHS = 40        # Увеличили с 10 до 40
    LR = 1e-3          # Learning rate
    DROPOUT = 0.1      # Dropout для регуляризации
    
    print("=" * 60)
    print("ОБУЧЕНИЕ ЯЗЫКОВОЙ МОДЕЛИ TRANSFORMER")
    print("=" * 60)
    
    # 1. Загрузка токенизатора
    print("\n1. Загрузка токенизатора...")
    tokenizer = BPETokenizer()
    
    if os.path.exists("bpe_tokenizer.json"):
        tokenizer.load("bpe_tokenizer.json")
    else:
        print("Токенизатор не найден. Сначала обучите токенизатор через bpe_tokenizer.py")
        return
    
    VOCAB_SIZE = len(tokenizer.vocab)
    print(f"Размер словаря: {VOCAB_SIZE}")
    
    # 2. Подготовка данных
    print("\n2. Подготовка данных...")
    train_texts, val_texts = prepare_data("data.txt", train_ratio=0.9)
    
    # 3. Создание даталоадера
    print("\n3. Создание даталоадера...")
    train_loader = DataLoader(train_texts, tokenizer, MAX_SEQ_LEN, BATCH_SIZE, shuffle=True)
    
    # 4. Инициализация модели
    print("\n4. Инициализация модели...")
    model = TransformerLM(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN,
        dropout=DROPOUT
    )
    
    # 5. Инициализация оптимизатора
    print("\n5. Инициализация оптимизатора...")
    optimizer = AdamOptimizer(learning_rate=LR, warmup_steps=1000)
    optimizer.init_params(model.get_parameters())
    
    # 6. Обучение
    print("\n6. Начало обучения...")
    train_losses = []
    train_accuracies = []
    val_losses = []
    val_accuracies = []
    
    best_val_acc = 0.0
    
    for epoch in range(1, EPOCHS + 1):
        print(f"\n--- Эпоха {epoch} ---")
        
        # Обучение
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, epoch)
        train_losses.append(train_loss)
        train_accuracies.append(train_acc)
        
        # Валидация
        val_loss, val_acc = validate(model, val_texts, tokenizer, MAX_SEQ_LEN, num_batches=20)
        val_losses.append(val_loss)
        val_accuracies.append(val_acc)
        
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2%}")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2%}")
        
        # Сохранение лучшей модели
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print(f"✨ Новая лучшая модель! Val Acc: {best_val_acc:.2%}")
            with open("best_model.pkl", 'wb') as f:
                pickle.dump(model, f)
        
        # Сохранение модели при достижении 60%
        if val_acc >= 0.60:
            print(f"🎉 Достигнута цель в 60% точности! Сохраняем модель...")
            with open(f"model_60percent_epoch{epoch}.pkl", 'wb') as f:
                pickle.dump(model, f)
        
        # Сохранение чекпоинта
        with open(f"model_epoch_{epoch}.pkl", 'wb') as f:
            pickle.dump({
                'model': model,
                'train_loss': train_loss,
                'train_acc': train_acc,
                'val_loss': val_loss,
                'val_acc': val_acc,
                'epoch': epoch
            }, f)
        
        # Генерация примера текста каждые 5 эпох
        if epoch % 5 == 0:
            print("\nПример генерации:")
            prompt = "The universe is"
            generated = generate_text(model, tokenizer, prompt, max_length=30)
            print(f"Prompt: {prompt}")
            print(f"Generated: {generated}")
    
    # 7. Построение графиков
    print("\n7. Построение графиков обучения...")
    plt.figure(figsize=(14, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss', marker='o', linewidth=2)
    plt.plot(val_losses, label='Validation Loss', marker='s', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accuracies, label='Train Accuracy', marker='o', linewidth=2)
    plt.plot(val_accuracies, label='Validation Accuracy', marker='s', linewidth=2)
    plt.axhline(y=0.60, color='r', linestyle='--', linewidth=2, label='60% target')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.title('Training and Validation Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_metrics.png', dpi=150)
    plt.show()
    
    # 8. Сохранение финальной модели
    print("\n8. Сохранение финальной модели...")
    with open("transformer_lm_final.pkl", 'wb') as f:
        pickle.dump({
            'model': model,
            'train_losses': train_losses,
            'train_accuracies': train_accuracies,
            'val_losses': val_losses,
            'val_accuracies': val_accuracies
        }, f)
    
    print(f"\nОбучение завершено!")
    print(f"Лучшая валидационная точность: {best_val_acc:.2%}")
    
    if best_val_acc >= 0.60:
        print("✅ Цель в 60% точности достигнута!")
    else:
        print(f"❌ Цель в 60% не достигнута. Нужно обучить еще {40 - EPOCHS} эпох или увеличить модель.")


if __name__ == "__main__":
    main()
