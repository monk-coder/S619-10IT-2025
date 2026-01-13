import random


class Perceptron:
    def __init__(self, num_inputs, learning_rate=0.1):
        self.weights = [random.uniform(-0.5, 0.5) for _ in range(num_inputs)]
        self.bias = random.uniform(-0.5, 0.5)
        self.learning_rate = learning_rate

    def activation(self, sum_value):
        if sum_value >= 0:
            return 1
        else:
            return 0

    def forward(self, inputs, labels, epochs=20):
        print("--- start params ---")
        print(f"w's: {self.weights}")
        print(f"b's: {self.bias}\n")

        print("--- learning ---")
        for epoch in range(epochs):
            total_error = 0
            for input_data, label in zip(inputs, labels):
                weighted_sum = 0
                for i in range(len(self.weights)):
                    weighted_sum += input_data[i] * self.weights[i]
                weighted_sum += self.bias

                prediction = self.activation(weighted_sum)
                error = label - prediction

                if error != 0:
                    total_error += 1
                    for i in range(len(self.weights)):
                        self.weights[i] = (
                            self.weights[i] + self.learning_rate * error * input_data[i]
                        )

                    self.bias = self.bias + self.learning_rate * error

            print(f"epoch {epoch + 1}: errors = {total_error}")
            if total_error == 0:
                print("no errors, finished learning")
                break

        print("final params")
        print(f"learned w's: {[round(w, 2) for w in self.weights]}")
        print(f"learned b's: {round(self.bias, 2)}\n")

    def backward(self, inputs, labels):
        print("model testing")
        for input_data, label in zip(inputs, labels):
            weighted_sum = 0
            for i in range(len(self.weights)):
                weighted_sum += input_data[i] * self.weights[i]
            weighted_sum += self.bias

            prediction = self.activation(weighted_sum)

            print(f"in: {input_data}, label: {label}, predict: {prediction}")


inputs = [[0, 0], [0, 1], [1, 0], [1, 1]]
labels = [0, 0, 0, 1]

perceptron = Perceptron(num_inputs=2, learning_rate=0.1)

perceptron.forward(inputs, labels, epochs=20)

perceptron.backward(inputs, labels)
