import numpy as np

# 1. Создание обучающего набора данных для логической функции AND
# Входы: [x1, x2]
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])

# Целевые выходы (метки) для AND: 1 только если оба входа = 1
y = np.array([0, 0, 0, 1])

# 2. Инициализация параметров перцептрона
np.random.seed(42)  # Для воспроизводимости результатов
weights = np.random.uniform(-0.5, 0.5, size=2)  # Веса для двух входов
bias = 0.0  # Начальное смещение
learning_rate = 0.1  # Коэффициент обучения
epochs = 20  # Количество эпох обучения

# 3. Функция активации (ступенчатая)
def step_function(x):
    """Возвращает 1, если x >= 0, иначе 0."""
    return 1 if x >= 0 else 0

# 4. Обучение перцептрона
print("Начало обучения...\n")
for epoch in range(epochs):
    total_error = 0
    for i in range(len(X)):
        # Вычисление взвешенной суммы
        weighted_sum = np.dot(weights, X[i]) + bias
        # Применение функции активации
        prediction = step_function(weighted_sum)
        # Ошибка = целевое значение - предсказание
        error = y[i] - prediction
        total_error += abs(error)

        # Обновление весов и смещения по правилу перцептрона
        weights += learning_rate * error * X[i]
        bias += learning_rate * error

    # Опционально: вывод ошибки по эпохам (для отладки)
    # print(f"Эпоха {epoch + 1}, суммарная ошибка: {total_error}")

    # Ранняя остановка, если обучение завершено
    if total_error == 0:
        print(f"Обучение завершено на эпохе {epoch + 1}")
        break

# 5. Тестирование и вывод результатов
print("\nФинальные параметры:")
print(f"Веса: [{weights[0]:.3f}, {weights[1]:.3f}]")
print(f"Смещение (bias): {bias:.3f}\n")

print("Результаты предсказаний:")
print("Вход\tОжидаемый\tПредсказание")
for i in range(len(X)):
    weighted_sum = np.dot(weights, X[i]) + bias
    prediction = step_function(weighted_sum)
    print(f"{X[i]}\t{y[i]}\t\t{prediction}")