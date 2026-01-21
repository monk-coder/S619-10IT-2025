import numpy as np

# 1. Создание набора данных 
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])
y = np.array([0, 0, 0, 1])  

# 2. Инициализация параметров
np.random.seed(42)  
weights = np.random.uniform(-0.5, 0.5, size=2)
bias = 0.0
learning_rate = 0.1
epochs = 20

# 3. Функции перцептрона
def predict(x):
    """Делает предсказание с помощью ступенчатой активации."""
    weighted_sum = np.dot(weights, x) + bias
    return 1 if weighted_sum >= 0 else 0

def update_weights(x, error, learning_rate):
    """Обновляет глобальные веса и смещение на основе ошибки."""
    global weights, bias
    weights += learning_rate * error * x
    bias += learning_rate * error

# 4. Цикл обучения
for epoch in range(epochs):
    total_error = 0
    for i in range(len(X)):
        x_i = X[i]
        y_true = y[i]
        y_pred = predict(x_i)
        error = y_true - y_pred
        total_error += abs(error)

        # Обновление параметров через отдельную функцию
        update_weights(x_i, error, learning_rate)

    # Опционально: досрочная остановка при нулевой ошибке
    if total_error == 0:
        print(f"Обучение сошлось на эпохе {epoch + 1}")
        break

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
