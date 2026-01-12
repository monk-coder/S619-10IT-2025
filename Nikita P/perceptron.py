import random

# 1. Данные для функции AND
X = [[0, 0], [0, 1], [1, 0], [1, 1]]
y = [0, 0, 0, 1]

# 2. Инициализация весов
weights = [random.uniform(-0.5, 0.5) for _ in range(2)]
bias = random.uniform(-0.5, 0.5)
learning_rate = 0.1
epochs = 20

print("Обучающие данные для AND:")
for i in range(4):
    print(f"  {X[i]} → {y[i]}")

print(f"\nНачальные веса: w1={weights[0]:.3f}, w2={weights[1]:.3f}, bias={bias:.3f}")
print()

# 3. Обучение перцептрона
for epoch in range(epochs):
    total_error = 0
    
    for i in range(len(X)):
        # Вычисление взвешенной суммы
        total = bias + X[i][0] * weights[0] + X[i][1] * weights[1]
        
        # Применение функции активации
        prediction = 1 if total >= 0 else 0
        
        # Вычисление ошибки
        error = y[i] - prediction
        total_error += abs(error)
        
        # Обновление весов
        weights[0] += learning_rate * error * X[i][0]
        weights[1] += learning_rate * error * X[i][1]
        bias += learning_rate * error
    
    print(f"Эпоха {epoch + 1:2d}, Ошибка: {total_error}")
    
    if total_error == 0:
        print("Обучение завершено!")
        break

# 4. Тестирование
print(f"\nФинальные веса: w1={weights[0]:.3f}, w2={weights[1]:.3f}, bias={bias:.3f}")
print("\nРезультаты тестирования:")
print("Входы | Ожидаемый | Предсказание")
print("-" * 30)

for i in range(len(X)):
    total = bias + X[i][0] * weights[0] + X[i][1] * weights[1]
    prediction = 1 if total >= 0 else 0
    print(f"{X[i]}   |     {y[i]}     |      {prediction}")
