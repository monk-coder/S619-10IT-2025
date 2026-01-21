X = [
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
]

y = [0, 0, 0, 1]

w1 = 0.0
w2 = 0.0
b = 0.0

learning_rate = 0.1
epochs = 20

def activation(value):
    if value >= 0:
        return 1
    return 0

for epoch in range(epochs):
    errors = 0
    for i in range(len(X)):
        x1, x2 = X[i]
        target = y[i]

        prediction = activation(w1 * x1 + w2 * x2 + b)
        error = target - prediction

        if error != 0:
            errors += 1

        w1 += learning_rate * error * x1
        w2 += learning_rate * error * x2
        b += learning_rate * error

    print(f"Эпоха {epoch + 1}: ошибок = {errors}")

    if errors == 0:
        break

print(f"\nФинальные веса и bias:")
print(f"w1 = {w1}, w2 = {w2}, b = {b}")
