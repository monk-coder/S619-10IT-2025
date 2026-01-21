import numpy as np

class Perceptron:
    def __init__(self, input_size, learning_rate=0.1, epochs=10):
        # Инициализация весов (включая смещение/bias) нулями
        self.weights = np.zeros(input_size + 1)
        self.lr = learning_rate
        self.epochs = epochs

    def activation_fn(self, x):
        # Ступенчатая функция активации (Heaviside step function)
        return 1 if x >= 0 else 0

    def predict(self, inputs):
        # Вычисление взвешенной суммы + смещение
        z = np.dot(inputs, self.weights[1:]) + self.weights[0]
        return self.activation_fn(z)

    def train(self, training_inputs, labels):
        for _ in range(self.epochs):
            for inputs, label in zip(training_inputs, labels):
                prediction = self.predict(inputs)
                # Правило обновления весов: w = w + lr * (ошибка) * x
                error = label - prediction
                self.weights[1:] += self.lr * error * inputs
                self.weights[0] += self.lr * error

# Пример использования: Логическое И (AND)
if __name__ == "__main__":
    # Данные для обучения (X1, X2)
    training_data = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])
    # Целевые значения (Y)
    labels = np.array([0, 0, 0, 1])

    # Создание и обучение модели
    perceptron = Perceptron(input_size=2)
    perceptron.train(training_data, labels)

    # Тестирование
    print("Результаты после обучения:")
    for x in training_data:
        print(f"Вход: {x}, Предсказание: {perceptron.predict(x)}")
