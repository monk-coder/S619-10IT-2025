# train.py
import numpy as np
import matplotlib.pyplot as plt
import pickle
from model import TransformerLM
from utils import Adam, cross_entropy_loss, cross_entropy_gradient, DataLoader, plot_losses, save_model


def main():
    # Параметры
    VOCAB_SIZE = 1000
    D_MODEL = 128
    N_HEAD = 4
    N_LAYER = 2
    MAX_SEQ_LEN = 64
    BATCH_SIZE = 16
    LR = 0.001
    EPOCHS = 5

    print("Создание модели...")
    model = TransformerLM(VOCAB_SIZE, D_MODEL, N_HEAD, N_LAYER, MAX_SEQ_LEN)

    # Получаем параметры модели
    params = model.get_params()
    print(f"Всего параметров: {sum(p[0].size for p in params)}")

    optimizer = Adam(params, lr=LR)

    # Данные
    print("Подготовка данных...")
    data = np.random.randint(0, VOCAB_SIZE, 10000)
    dataloader = DataLoader(data, BATCH_SIZE, MAX_SEQ_LEN)

    losses = []

    for epoch in range(EPOCHS):
        epoch_loss = 0
        n_batches = 0

        print(f"\nЭпоха {epoch + 1}/{EPOCHS}")

        for x, y in dataloader:
            # Forward
            logits = model.forward(x)
            loss = cross_entropy_loss(logits, y)
            epoch_loss += loss

            # Backward
            dlogits = cross_entropy_gradient(logits, y)
            model.backward(dlogits)

            # Update
            optimizer.step()
            optimizer.zero_grad()
            model.zero_grad()

            n_batches += 1

            if n_batches % 10 == 0:
                print(f"  Батч {n_batches}, Loss: {loss:.4f}")

        avg_loss = epoch_loss / n_batches
        losses.append(avg_loss)
        print(f"Средний Loss за эпоху: {avg_loss:.4f}")

        # Генерируем пример
        if (epoch + 1) % 2 == 0:
            prompt = data[:20]
            generated = model.generate(prompt, max_new_tokens=20, temperature=0.8, top_k=40)
            print(f"Пример генерации: {generated[:30]}...")

    # Сохраняем модель и график
    save_model(model, 'model.pkl')
    plot_losses(losses, 'loss.png')

    print("\nОбучение завершено!")


if __name__ == "__main__":
    main()