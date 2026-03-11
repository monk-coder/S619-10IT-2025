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
    
    for _ in range(max_length):
        # Обрезаем до максимальной длины
        if input_ids
