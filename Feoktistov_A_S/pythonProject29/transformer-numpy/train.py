import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import pickle
import os
import sys

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.transformer_lm import TransformerLM
from utils.optimizer import Adam
from utils.loss import cross_entropy_loss, cross_entropy_gradient
from data.dataset import TextDataset, DataLoader


def train_epoch(model, dataloader, optimizer):
    total_loss = 0
    n_batches = 0

    for x, y in dataloader:
        # Forward pass
        logits = model.forward(x)

        # Вычисляем loss
        loss = cross_entropy_loss(logits, y)
        total_loss += loss

        # Backward pass
        dlogits = cross_entropy_gradient(logits, y)
        model.backward(dlogits)

        # Обновляем веса
        optimizer.step()
        optimizer.zero_grad()
        model.zero_grad()

        n_batches += 1

    return total_loss / n_batches


def main():
    # Гиперпараметры
    VOCAB_SIZE = 1000
    D_MODEL = 128
    N_HEAD = 4
    N_LAYER = 2
    MAX_SEQ_LEN = 64
    BATCH_SIZE = 16
    LR = 0.001
    N_EPOCHS = 5

    print("Создание модели...")
    model = TransformerLM(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN
    )

    print("Создание оптимизатора...")
    optimizer = Adam(model.get_parameters(), lr=LR)

    # Создаем тестовые данные
    print("Подготовка данных...")
    tokens = np.random.randint(0, VOCAB_SIZE, 10000)
    dataset = TextDataset(tokens, MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, BATCH_SIZE, shuffle=True)

    # Обучение
    train_losses = []

    for epoch in range(N_EPOCHS):
        print(f"Эпоха {epoch + 1}/{N_EPOCHS}")
        loss = train_epoch(model, dataloader, optimizer)
        train_losses.append(loss)
        print(f"Loss: {loss:.4f}")

        # Генерируем пример
        if (epoch + 1) % 2 == 0:
            prompt = tokens[:20]
            generated = model.generate(prompt, max_new_tokens=20, temperature=0.8, top_k=40)
            print(f"Пример генерации: {generated[:30]}...")

    # Сохраняем модель
    os.makedirs('checkpoints', exist_ok=True)
    with open('checkpoints/model.pkl', 'wb') as f:
        pickle.dump(model, f)

    # Рисуем график
    os.makedirs('logs', exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses)
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.savefig('logs/training_loss.png')
    plt.show()

    print("Обучение завершено!")


if __name__ == "__main__":
    main()