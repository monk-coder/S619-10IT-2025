import torch
import torch.optim as optim
import numpy as np
import os
import time
from tqdm import tqdm

from config import get_args
from model import GPT
from data import load_data, BPEEncoder
from utils import estimate_loss, save_checkpoint, get_lr_scheduler, calculate_perplexity


def main():
    args = get_args()

    # Проверяем наличие файла данных
    if not os.path.exists(args.data_path):
        print(f"❌ Ошибка: файл {args.data_path} не найден!")
        print("Создайте файл data.txt с текстом для обучения")
        print("или укажите путь к существующему файлу: python train.py --data_path=путь_к_файлу")
        return

    print(f"✅ Файл данных найден: {args.data_path}")

    # Создаем директорию для чекпоинтов
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    # Читаем текст для энкодера
    with open(args.data_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # Проверяем размер данных
    if len(full_text) < 100:
        print(f"⚠️ Внимание: текст слишком короткий ({len(full_text)} символов)")
        print("Для качественного обучения нужно больше данных")

    # Загружаем или создаем BPE энкодер
    encoder_path = os.path.join(args.checkpoint_dir, 'bpe_encoder.pt')
    encoder = BPEEncoder(args.vocab_size)

    if os.path.exists(encoder_path):
        print(f"Загрузка энкодера из {encoder_path}")
        encoder.load(encoder_path)
    else:
        print("Обучение BPE энкодера...")
        encoder.train(full_text)
        encoder.save(encoder_path)
        print(f"✅ Энкодер сохранен в {encoder_path}")
        print(f"Размер словаря: {len(encoder.char_to_idx)}")

    # Загружаем данные
    print("Загрузка данных...")
    train_loader, val_loader, vocab_size = load_data(
        args.data_path, encoder, args.block_size,
        args.batch_size, args.device
    )

    print(f"Размер словаря: {vocab_size}")
    print(f"Количество батчей в train: {len(train_loader)}")
    print(f"Количество батчей в val: {len(val_loader)}")

    # Проверяем, что данные не пустые
    if len(train_loader) == 0:
        print("❌ Ошибка: недостаточно данных для обучения!")
        print(f"Длина текста: {len(full_text)} символов")
        print(f"Block size: {args.block_size}")
        print("Увеличьте размер текста или уменьшите block_size")
        return

    # Создаем модель
    print("Создание модели...")
    model = GPT(
        vocab_size=vocab_size,
        embed_dim=args.embed_dim,
        num_heads=args.num_heads,
        num_layers=args.num_layers,
        block_size=args.block_size
    )

    # Перемещаем на устройство
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    print(f"Используется устройство: {device}")

    # Подсчет параметров
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Всего параметров: {total_params:,}")
    print(f"Обучаемых параметров: {trainable_params:,}")

    # Оптимизатор AdamW
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay
    )

    # Scheduler с warmup
    scheduler = get_lr_scheduler(optimizer, args.warmup_iters, args.max_iters)

    # Mixed precision
    scaler = torch.cuda.amp.GradScaler() if args.mixed_precision and device.type == 'cuda' else None

    # Переменные для отслеживания
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    times = []

    print(f"\nНачало обучения на {args.max_iters} итераций")
    print("=" * 60)

    # Основной цикл обучения
    step = 0
    train_iter = iter(train_loader)

    for step in range(args.max_iters):
        start_time = time.time()

        # Получаем батч
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_loader)
            x, y = next(train_iter)

        x, y = x.to(device), y.to(device)

        # Forward pass с mixed precision
        if scaler:
            with torch.cuda.amp.autocast():
                _, loss = model(x, y)
        else:
            _, loss = model(x, y)

        # Backward pass
        optimizer.zero_grad(set_to_none=True)

        if scaler:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()

        scheduler.step()

        # Замер времени
        step_time = time.time() - start_time
        times.append(step_time)

        # Оценка на валидации
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            val_loss = estimate_loss(model, val_loader, args.eval_iters, device)
            val_perplexity = calculate_perplexity(val_loss)

            train_losses.append(loss.item())
            val_losses.append(val_loss)

            print(f"\nШаг {step}:")
            print(f"  Train loss: {loss.item():.4f}")
            print(f"  Val loss: {val_loss:.4f}")
            print(f"  Val perplexity: {val_perplexity:.2f}")
            print(f"  LR: {optimizer.param_groups[0]['lr']:.6f}")
            print(f"  Время на шаг: {step_time * 1000:.2f}ms")

            # Сохраняем лучшую модель
            is_best = val_loss < best_val_loss
            if is_best:
                best_val_loss = val_loss
                print(f"  *** Новая лучшая модель! ***")

            save_checkpoint(model, optimizer, scheduler, step, val_loss,
                            args.checkpoint_dir, is_best)

        # Регулярное сохранение
        if step > 0 and step % args.save_interval == 0:
            save_checkpoint(model, optimizer, scheduler, step, loss.item(),
                            args.checkpoint_dir, False)

    # Финальная статистика
    print("\n" + "=" * 60)
    print("Обучение завершено!")
    print(f"Лучшая val loss: {best_val_loss:.4f}")
    print(f"Лучшая perplexity: {calculate_perplexity(best_val_loss):.2f}")
    print(f"Среднее время на шаг: {np.mean(times) * 1000:.2f}ms")
    print(f"Итераций в секунду: {1 / np.mean(times):.2f}")

    # Сохраняем историю обучения
    np.save(os.path.join(args.checkpoint_dir, 'train_losses.npy'), train_losses)
    np.save(os.path.join(args.checkpoint_dir, 'val_losses.npy'), val_losses)


if __name__ == "__main__":
    main()