# train.py
import numpy as np
import os
import sys
from model import TransformerLM
from utils import (
    Adam, DataLoader, cross_entropy_loss, cross_entropy_gradient,
    load_text, create_vocab, text_to_indices, save_checkpoint, plot_losses
)


def main():
    # ==================== ПАРАМЕТРЫ ====================
    # Параметры модели
    D_MODEL = 128  # размер эмбеддингов
    N_HEAD = 4  # количество голов внимания
    N_LAYER = 2  # количество слоев трансформера
    MAX_SEQ_LEN = 64  # максимальная длина последовательности

    # Параметры обучения
    BATCH_SIZE = 16  # размер батча
    LR = 0.001  # learning rate
    EPOCHS = 10  # количество эпох

    # Параметры данных
    DATA_FILE = 'data.txt'  # файл с текстом

    # ==================== ПРОВЕРКА ФАЙЛА ====================
    if not os.path.exists(DATA_FILE):
        print(f"ОШИБКА: Файл {DATA_FILE} не найден!")
        print("Создайте файл data.txt с текстом для обучения.")
        print("\nПример создания файла:")
        print('echo "Привет мир! Это текст для обучения." > data.txt')
        return

    # ==================== ЗАГРУЗКА ДАННЫХ ====================
    print("=" * 60)
    print("ЗАГРУЗКА ДАННЫХ")
    print("=" * 60)

    # Загружаем текст
    text = load_text(DATA_FILE)
    print(f"Загружено {len(text)} символов")
    print(f"Первые 200 символов:\n{text[:200]}\n")

    # Создаем словарь
    char_to_idx, idx_to_char, vocab_size = create_vocab(text)
    print(f"Размер словаря: {vocab_size} уникальных символов")
    print(f"Примеры символов: {list(char_to_idx.keys())[:20]}\n")

    # Преобразуем текст в индексы
    data = text_to_indices(text, char_to_idx)
    print(f"Данные преобразованы в {len(data)} индексов")

    # ==================== СОЗДАНИЕ МОДЕЛИ ====================
    print("=" * 60)
    print("СОЗДАНИЕ МОДЕЛИ")
    print("=" * 60)

    model = TransformerLM(
        vocab_size=vocab_size,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN
    )

    # Считаем количество параметров
    params = model.get_params()
    total_params = sum(p[0].size for p in params)
    print(f"Всего параметров: {total_params:,}")

    # Создаем оптимизатор и загрузчик данных
    optimizer = Adam(params, lr=LR)
    dataloader = DataLoader(data, BATCH_SIZE, MAX_SEQ_LEN)
    print(f"Количество батчей за эпоху: {len(dataloader)}")

    # ==================== ОБУЧЕНИЕ ====================
    print("=" * 60)
    print("ОБУЧЕНИЕ")
    print("=" * 60)

    losses = []

    for epoch in range(EPOCHS):
        epoch_loss = 0
        n_batches = 0

        print(f"\n--- Эпоха {epoch + 1}/{EPOCHS} ---")

        for batch_idx, (x, y) in enumerate(dataloader):
            # Forward pass
            logits = model.forward(x)
            loss = cross_entropy_loss(logits, y)
            epoch_loss += loss

            # Backward pass
            dlogits = cross_entropy_gradient(logits, y)
            model.backward(dlogits)

            # Update weights
            optimizer.step()
            optimizer.zero_grad()
            model.zero_grad()

            n_batches += 1

            # Выводим прогресс каждые 10 батчей
            if (batch_idx + 1) % 10 == 0:
                print(f"  Батч {batch_idx + 1}/{len(dataloader)}, Loss: {loss:.4f}")

        avg_loss = epoch_loss / n_batches
        losses.append(avg_loss)
        print(f"✓ Средний Loss за эпоху: {avg_loss:.4f}")

        # Генерируем пример текста после каждой эпохи
        if epoch == 0 or (epoch + 1) % 2 == 0:
            prompt = data[:20]  # первые 20 символов как промпт
            generated = model.generate(prompt, max_new_tokens=100, temperature=0.8, top_k=40)

            # Преобразуем индексы обратно в текст
            generated_text = ''.join([idx_to_char.get(i, '?') for i in generated])
            print(f"\nСгенерированный текст после эпохи {epoch + 1}:")
            print(f"{generated_text[:200]}...\n")

        # Сохраняем чекпоинт после каждой эпохи
        save_checkpoint(model, char_to_idx, idx_to_char, losses, f'checkpoint_epoch_{epoch + 1}.pkl')

    # ==================== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ====================
    print("=" * 60)
    print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    # Сохраняем финальную модель
    save_checkpoint(model, char_to_idx, idx_to_char, losses, 'final_model.pkl')

    # Рисуем график потерь
    plot_losses(losses, 'training_loss.png')

    # ==================== ФИНАЛЬНАЯ ГЕНЕРАЦИЯ ====================
    print("=" * 60)
    print("ФИНАЛЬНАЯ ГЕНЕРАЦИЯ")
    print("=" * 60)

    # Генерируем финальный пример
    prompt = data[:30]  # первые 30 символов как промпт
    generated = model.generate(prompt, max_new_tokens=200, temperature=0.7, top_k=40)
    generated_text = ''.join([idx_to_char.get(i, '?') for i in generated])

    print(f"\nПромпт: {text[:30]}")
    print(f"\nСгенерированный текст (первые 500 символов):")
    print(f"{generated_text[:500]}...")

    # Сохраняем сгенерированный текст в файл
    with open('generated.txt', 'w', encoding='utf-8') as f:
        f.write(generated_text)
    print("\nПолный текст сохранен в generated.txt")

    print("\n" + "=" * 60)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)
    print(f"Финальный loss: {losses[-1]:.4f}")
    print(f"Модель сохранена в final_model.pkl")
    print(f"График потерь сохранен в training_loss.png")


if __name__ == "__main__":
    main()