import numpy as np


X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])


y = np.array([0, 1, 1, 1])


np.random.seed(42)
weights = np.random.randn(2)
bias = np.random.randn()


learning_rate = 0.1
epochs = 10

for epoch in range(epochs):
    total_error = 0
    for input_vector, target in zip(X, y):

        linear_output = np.dot(input_vector, weights) + bias

        prediction = 1 if linear_output >= 0 else 0

        error = target - prediction
        total_error += abs(error)

        weights += learning_rate * error * input_vector
        bias += learning_rate * error
    print(f"Эпоха {epoch+1}: ошибка {total_error}")


print("\nОбученные веса:", weights)
print("Обученное смещение:", bias)
print("Результаты после обучения:")
for input_vector in X:
    linear_output = np.dot(input_vector, weights) + bias
    prediction = 1 if linear_output >= 0 else 0
    print(f"Вход: {input_vector} -> Предсказание: {prediction}")