import random


class Perceptron:
    """
    main class for simple perZeptron
    """

    def __init__(self, num_inputs, learning_rate=0.1):
        """
        just a regular init
        """
        self.weights = [random.uniform(-0.5, 0.5) for _ in range(num_inputs)]
        self.bias = random.uniform(-0.5, 0.5)
        self.learning_rate = learning_rate

    def activation(self, sum_value):
        """
        porogovaya aktivatsiya
        """
        if sum_value >= 0:
            return 1
        else:
            return 0

    def forward(self, inputs, labels):
        """
        testing model
        """
        print("--- testing ts ---")
        for input_data, label in zip(inputs, labels):
            weighted_sum = 0
            for i in range(len(self.weights)):
                weighted_sum += input_data[i] * self.weights[i]
            weighted_sum += self.bias
            prediction = self.activation(weighted_sum)
            print(f"input: {input_data}, label: {label}, predict: {prediction}")
    def backward(self, inputs, labels, epochs=20):
        """
        korrektiruet vse chto nado
        """
        print("--- start params ---")
        print(f"weights: {self.weights}")
        print(f"bias: {self.bias}\n")
        print("--- learning---")
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
            print(f"epoch {epoch + 1}: erores = {total_error}")
            if total_error == 0:
                print("no erores finished learning")
                break
        print("\n--- final params ---")
        print(f"learned weights: {[round(w, 2) for w in self.weights]}")
        print(f"learned bias: {round(self.bias, 2)}\n")

>>>>>>> 64f01f1 (asd):Goncharov_A_A/2_half/perceptron.py

inputs = [[0, 0], [0, 1], [1, 0], [1, 1]]
labels = [0, 0, 0, 1]
perceptron = Perceptron(num_inputs=2, learning_rate=0.1)
perceptron.backward(inputs, labels, epochs=20)
perceptron.forward(inputs, labels)
