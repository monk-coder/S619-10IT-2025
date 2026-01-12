import random

inputs = [[0, 0], [0, 1], [1, 0], [1, 1]]
labels = [0, 0, 0, 1]

weights = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]

bias = random.uniform(-0.5, 0.5)

learning_rate = 0.1

epochs = 20

print("--- start params ---")
print(f"w's: {weights}")
print(f"b's: {bias}\n")


def activation(sum_value):
    if sum_value >= 0:
        return 1
    else:
        return 0


print("--- learning ---")
for epoch in range(epochs):
    total_error = 0
    for input_data, label in zip(inputs, labels):
        weighted_sum = (
            (input_data[0] * weights[0]) + (input_data[1] * weights[1]) + bias
        )
        prediction = activation(weighted_sum)
        error = label - prediction

        if error != 0:
            total_error += 1
            weights[0] = weights[0] + learning_rate * error * input_data[0]
            weights[1] = weights[1] + learning_rate * error * input_data[1]

            bias = bias + learning_rate * error

    print(f"epoch {epoch + 1}: errors = {total_error}")
    if total_error == 0:
        print("no errors, finished learning")
        break

print("final params")
print(f"learned w's: {[round(w, 2) for w in weights]}")
print(f"learned b's: {round(bias, 2)}\n")

print("model testing")
for input_data, label in zip(inputs, labels):
    weighted_sum = (input_data[0] * weights[0]) + (input_data[1] * weights[1]) + bias
    prediction = activation(weighted_sum)

    print(f"in: {input_data}, label: {label}, predict: {prediction}")
