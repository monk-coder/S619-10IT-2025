# Однослойный перцептрон для логической функции AND

# 1. Набор данных
# Входные данные (x1, x2)
X = [
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
]

# Целевые значения (AND)
y = [0, 0, 0, 1]

# 2. Инициализация параметров
weights = [0.0, 0.0]   # веса w1 и w2
bias = 0.0             # смещение
learning_rate = 0.1
epochs = 20

# 3. Функции перцептрона
def weighted_sum(x, w, b):
    """Вычисляет взвешенную сумму"""
    return x[0] * w[0] + x[1] * w[1] + b

def activation(value):
    """Ступенчатая функция активации"""
    return 1 if value >= 0 else 0

# 4. Цикл обучения
for epoch in range(epochs):
    for i in range(len(X)):
        x = X[i]
        target = y[i]

        # Предсказание
        output = activation(weighted_sum(x, weights, bias))

        # Ошибка
        error = target - output

        # Обновление весов и смещения
        weights[0] += learning_rate * error * x[0]
        weights[1] += learning_rate * error * x[1]
        bias += learning_rate * error

# 5. Результаты
print("Финальные веса:", weights)
print("Финальное смещение (bias):", bias)
print("\nПроверка работы перцептрона:")

for i in range(len(X)):
    prediction = activation(weighted_sum(X[i], weights, bias))
    print(f"Вход: {X[i]}, Ожидалось: {y[i]}, Предсказание: {prediction}")