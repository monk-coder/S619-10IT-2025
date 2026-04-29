"""
Численная проверка градиентов для PyTorch модели.
"""

import torch
import torch.nn as nn
from model import GPT


def create_causal_mask(seq_len, device):
    return torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()


def numerical_gradient_check(model, x, y, eps=1e-5):
    """Проверяет градиенты численным методом."""
    model.train()

    # Генерация маски для корректного forward-прохода
    mask = create_causal_mask(x.shape[1], x.device)

    # Forward + backward
    logits = model(x, mask)
    loss = nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))
    loss.backward()

    max_diff = 0

    for name, param in model.named_parameters():
        if param.grad is None:
            continue

        grad_analytical = param.grad.clone()

        # Проверяем несколько случайных параметров
        indices = torch.randint(0, param.numel(), (min(5, param.numel()),))

        for idx in indices:
            original = param.data.view(-1)[idx].clone()

            # f(x + eps)
            param.data.view(-1)[idx] = original + eps
            logits_plus = model(x, mask)
            loss_plus = nn.functional.cross_entropy(logits_plus.view(-1, logits_plus.size(-1)), y.view(-1))

            # f(x - eps)
            param.data.view(-1)[idx] = original - eps
            logits_minus = model(x, mask)
            loss_minus = nn.functional.cross_entropy(logits_minus.view(-1, logits_minus.size(-1)), y.view(-1))

            # Восстанавливаем
            param.data.view(-1)[idx] = original

            grad_numerical = (loss_plus - loss_minus) / (2 * eps)
            grad_analytical_val = grad_analytical.view(-1)[idx]

            diff = abs(grad_numerical - grad_analytical_val) / (abs(grad_numerical) + abs(grad_analytical_val) + 1e-8)
            max_diff = max(max_diff, diff.item())

    return max_diff


def main():
    print("=" * 50)
    print("ЧИСЛЕННАЯ ПРОВЕРКА ГРАДИЕНТОВ")
    print("=" * 50)

    model = GPT(vocab_size=100, d_model=32, n_head=2, n_layer=2, d_ff=64, seq_len=16)

    x = torch.randint(0, 100, (4, 16))
    y = torch.randint(0, 100, (4, 16))

    max_err = numerical_gradient_check(model, x, y)

    print(f"\nМаксимальная ошибка градиента: {max_err:.2e}")

    if max_err < 1e-4:
        print("✅ Градиенты верны!")
    else:
        print("❌ Ошибка в градиентах!")


if __name__ == '__main__':
    main()