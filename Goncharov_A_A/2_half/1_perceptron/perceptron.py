import random


class Perceptron:
    def __init__(self, num_inputs, learning_rate=0.1):
        self.weights = [random.uniform(-0.5, 0.5) for _ in range(num_inputs)]
        self.bias = random.uniform(-0.5, 0.5)
        self.learning_rate = learning_rate

    def activation(self, sum_value):
        return 1 if sum_value >= 0 else 0

    def forward(self, inputs, labels):
        updates = []
        total_error = 0
        for input_data, label in zip(inputs, labels):
            weighted_sum = (
                sum(i * w for i, w in zip(input_data, self.weights)) + self.bias
            )
            prediction = self.activation(weighted_sum)
            error = label - prediction
            if error != 0:
                total_error += 1
                updates.append((error, input_data))
        return total_error, updates

    def backward(self, updates):
        for error, input_data in updates:
            for i in range(len(self.weights)):
                self.weights[i] += self.learning_rate * error * input_data[i]
            self.bias += self.learning_rate * error

    def test(self, inputs, labels):
        print("--- testing ts ---")
        for input_data, label in zip(inputs, labels):
            weighted_sum = (
                sum(i * w for i, w in zip(input_data, self.weights)) + self.bias
            )
            prediction = self.activation(weighted_sum)
            print(f"input: {input_data}, label: {label}, predict: {prediction}")


inputs = [[0, 0], [0, 1], [1, 0], [1, 1]]
labels = [0, 0, 0, 1]
epochs = 20

perceptron = Perceptron(num_inputs=2, learning_rate=0.1)

print("--- learning---")
for epoch in range(epochs):
    total_error, updates = perceptron.forward(inputs, labels)
    if total_error == 0:
        print(f"epoch {epoch + 1}: erores = {total_error}")
        print("no erores finished learning")
        break

    perceptron.backward(updates)
    print(f"epoch {epoch + 1}: erores = {total_error}")

print("\n--- final params ---")
print(f"learned weights: {[round(w, 2) for w in perceptron.weights]}")
print(f"learned bias: {round(perceptron.bias, 2)}\n")

perceptron.test(inputs, labels)
