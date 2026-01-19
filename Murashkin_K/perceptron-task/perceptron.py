import numpy as np

inputs = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])
targets = np.array([0, 0, 0, 1])


np.random.seed(42)
weights = np.random.uniform(-0.1, 0.1, size=2)
bias = np.random.uniform(-0.1, 0.1)
learning_rate = 0.1
epochs = 20

print(f"Начальные веса: w1={weights[0]:.3f}, w2={weights[1]:.3f}")
print(f"Начальное смещение: b={bias:.3f}")


def compute_weighted_sum(inputs, weights, bias):
    return np.dot(inputs, weights) + bias


def activation_function(sum_value):
    return 1 if sum_value >= 0 else 0


for epoch in range(epochs):
    total_error = 0
    for i in range(len(inputs)):
        weighted_sum = compute_weighted_sum(inputs[i], weights, bias)
        prediction = activation_function(weighted_sum)

        error = targets[i] - prediction

        weights[0] += learning_rate * error * inputs[i][0]
        weights[1] += learning_rate * error * inputs[i][1]
        bias += learning_rate * error

        total_error += abs(error)

    if epoch % 5 == 0 or epoch == epochs - 1:
        print(f"Эпоха {epoch}: общая ошибка = {total_error}")

print("\n=== Результаты обучения ===")
print(f"Финальные веса: w1={weights[0]:.3f}, w2={weights[1]:.3f}")
print(f"Финальное смещение: b={bias:.3f}")
print("Вход | Ожидаемый | Предсказание")
print("-" * 35)

for i in range(len(inputs)):
    weighted_sum = compute_weighted_sum(inputs[i], weights, bias)
    prediction = activation_function(weighted_sum)
    print(f"({inputs[i][0]},{inputs[i][1]}) | {targets[i]} | {prediction}")

