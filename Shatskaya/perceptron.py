import numpy as np

inputs = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])

targets = np.array([0, 0, 0, 1])

weights = np.array([0.0, 0.0])
bias = 0.0
learning_rate = 0.1
epochs = 20

def predict(x):
    sum_val = weights[0]*x[0] + weights[1]*x[1] + bias
    return 1 if sum_val >= 0 else 0

for epoch in range(epochs):
    for i in range(4):
        x = inputs[i]
        target = targets[i]
        prediction = predict(x)
        error = target - prediction
        weights[0] += learning_rate * error * x[0]
        weights[1] += learning_rate * error * x[1]
        bias += learning_rate * error

print("Финальные веса:", weights)
print("Bias:", bias)
print("\nРезультаты:")

for i in range(4):
    x = inputs[i]
    pred = predict(x)
    print(f"{x} → должно быть {targets[i]}, получилось {pred}")