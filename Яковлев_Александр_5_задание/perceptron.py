
# Реализация однослойного перцептрона для обучения логической функции AND

import numpy as np

# 1. Создание набора данных (логическая функция AND)
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])
y = np.array([0, 0, 0, 1])  # Целевые значения для AND

# 2. Инициализация параметров
np.random.seed(42)  # Для воспроизводимости
weights = np.random.uniform(-0.5, 0.5, size=2)  # Веса для двух входов
bias = 0.0  # Начальное смещение
learning_rate = 0.1
epochs = 20  # Количество эпох обучения

# 3. Функции перцептрона
def predict(x):
    """Вычисляет предсказание перцептрона с использованием ступенчатой активации."""
    weighted_sum = np.dot(weights, x) + bias
    return 1 if weighted_sum >= 0 else 0

# 4. Цикл обучения
for epoch in range(epochs):
    total_error = 0
    for i in range(len(X)):
        x_i = X[i]
        y_true = y[i]
        y_pred = predict(x_i)
        error = y_true - y_pred
        total_error += abs(error)

        # Обновление весов и смещения по правилу перцептрона
        weights += learning_rate * error * x_i
        bias += learning_rate * error

    # Опционально: вывод ошибки по эпохам (для отладки)
    # print(f"Эпоха {epoch + 1}, суммарная ошибка: {total_error}")

# 5. Тестирование и вывод результатов
print("Обучение завершено!")
print(f"Финальные веса: w1 = {weights[0]:.3f}, w2 = {weights[1]:.3f}")
print(f"Финальное смещение (bias): {bias:.3f}\n")

print("Результаты предсказаний:")
print("Вход\tОжидаемый\tПредсказание")
for i in range(len(X)):
    x_i = X[i]
    y_true = y[i]
    y_pred = predict(x_i)
    print(f"{x_i}\t{y_true}\t\t{y_pred}")
