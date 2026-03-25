import numpy as np
import matplotlib.pyplot as plt
import os
import argparse


def get_args():
    parser = argparse.ArgumentParser(description='Визуализация потерь обучения')
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                        help='Директория с чекпоинтами')
    return parser.parse_args()


def main():
    args = get_args()

    # Загружаем потери
    train_losses_path = os.path.join(args.checkpoint_dir, 'train_losses.npy')
    val_losses_path = os.path.join(args.checkpoint_dir, 'val_losses.npy')

    if not os.path.exists(train_losses_path):
        print(f"❌ Файл {train_losses_path} не найден!")
        return

    train_losses = np.load(train_losses_path)
    val_losses = np.load(val_losses_path)

    # Создаем график
    plt.figure(figsize=(12, 5))

    # График потерь
    plt.subplot(1, 2, 1)
    steps = np.arange(len(train_losses)) * 500  # eval_interval
    plt.plot(steps, train_losses, label='Train Loss', alpha=0.7)
    plt.plot(steps, val_losses, label='Val Loss', alpha=0.7)
    plt.xlabel('Шаг')
    plt.ylabel('Loss')
    plt.title('Потери на обучении и валидации')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # График perplexity
    plt.subplot(1, 2, 2)
    train_perplexity = np.exp(train_losses)
    val_perplexity = np.exp(val_losses)
    plt.plot(steps, train_perplexity, label='Train Perplexity', alpha=0.7)
    plt.plot(steps, val_perplexity, label='Val Perplexity', alpha=0.7)
    plt.xlabel('Шаг')
    plt.ylabel('Perplexity')
    plt.title('Perplexity на обучении и валидации')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Сохраняем график
    save_path = os.path.join(args.checkpoint_dir, 'training_curves.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✅ График сохранен в {save_path}")

    # Показываем
    plt.show()

    # Выводим статистику
    print(f"\nСтатистика:")
    print(f"  Лучшая val loss: {np.min(val_losses):.4f}")
    print(f"  Лучшая perplexity: {np.exp(np.min(val_losses)):.2f}")
    print(f"  Финальная val loss: {val_losses[-1]:.4f}")
    print(f"  Финальная perplexity: {np.exp(val_losses[-1]):.2f}")


if __name__ == "__main__":
    main()