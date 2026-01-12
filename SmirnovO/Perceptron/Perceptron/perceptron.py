# Однослойный перцептрон для логической функции AND
# Данные: входы [[0,0], [0,1], [1,0], [1,1]], выходы [0,0,0,1]

import numpy as np
import random

# Набор данных для AND
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([0, 0, 0, 1])

# Инициализация весов и смещения (маленькие случайные значения)
np.random.seed(42)  # Для воспроизводимости
w1 = np.random.uniform(-0.1, 0.1)
w2 = np.random.uniform(-0.1, 0.1)
b = np.random.uniform(-0.1, 0.1)

learning_rate = 0.1
epochs = 20


def perceptron_output(x1, x2):
    """Вычисляет взвешенную сумму w1*x1 + w2*x2 + b"""
    z = w1 * x1 + w2 * x2 + b
    return 1 if z >= 0 else 0


print("Начальные веса: w1={}, w2={}, b={}".format(round(w1, 3), round(w2, 3), round(b, 3)))
print("\nОбучение ({})".format(epochs))

# Цикл обучения
for epoch in range(epochs):
    for i in range(len(X)):
        x1, x2 = X[i]
        target = y[i]
        prediction = perceptron_output(x1, x2)
        error = target - prediction

        # Обновление весов и смещения
        w1 += learning_rate * error * x1
        w2 += learning_rate * error * x2
        b += learning_rate * error

    if (epoch + 1) % 10 == 0:
        print("Эпоха {} завершена".format(epoch + 1))

print("\nФинальные веса: w1={}, w2={}, b={}".format(round(w1, 3), round(w2, 3), round(b, 3)))

# Тестирование
print("\nТестирование перцептрона:")
print("Вход\tОжидаемый\tПредсказание")
for i in range(len(X)):
    x1, x2 = X[i]
    pred = perceptron_output(x1, x2)
    print("[{0}, {1}]\t{2}\t\t{3}".format(x1, x2, y[i], pred))
