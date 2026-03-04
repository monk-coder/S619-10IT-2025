import numpy as np
import sys

sys.path.append('../..')

from models.transformer_lm import TransformerLM


def numerical_gradient(model, x, y, param_idx, epsilon=1e-5):
    """Численная проверка градиента для конкретного параметра"""
    params = model.get_parameters()
    param, _ = params[param_idx]
    original = param.copy()

    # Положительное возмущение
    param += epsilon
    logits = model.forward(x)
    loss_plus = cross_entropy_loss(logits, y)

    # Отрицательное возмущение
    param[:] = original - epsilon
    logits = model.forward(x)
    loss_minus = cross_entropy_loss(logits, y)

    # Восстанавливаем параметр
    param[:] = original

    # Численный градиент
    grad_num = (loss_plus - loss_minus) / (2 * epsilon)
    return grad_num


def test_gradient():
    # Маленькая модель для теста
    model = TransformerLM(
        vocab_size=100,
        d_model=32,
        n_head=2,
        n_layer=2,
        max_seq_len=16
    )

    # Случайные данные
    B, T = 2, 8
    x = np.random.randint(0, 100, (B, T))
    y = np.random.randint(0, 100, (B, T))

    # Forward
    logits = model.forward(x)
    loss = cross_entropy_loss(logits, y)

    # Backward
    dlogits = cross_entropy_gradient(logits, y)
    model.backward(dlogits)

    # Проверяем градиенты для первого параметра
    params = model.get_parameters()
    param, grad = params[0]

    # Берем один элемент для проверки
    idx = (0, 0)
    grad_num = numerical_gradient(model, x, y, 0, idx)

    relative_error = abs(grad[idx] - grad_num) / (abs(grad[idx]) + abs(grad_num) + 1e-8)
    assert relative_error < 1e-4, f"Gradient error too high: {relative_error}"

    print("Gradient check passed!")


if __name__ == "__main__":
    test_gradient()