# perceptron.py

import numpy as np

class Perceptron:
    def __init__(self, input_size=2, learning_rate=0.1, epochs=20):
        self.weights = np.random.randn(input_size)  # случайные небольшие веса
        self.bias = 0.0  # начальное смещение
        self.lr = learning_rate  # коэффициент обучения
        self.epochs = epochs  # количество эпох

    def activation(self, x):
        # Ступенчатая функция активации
        return 1 if x >= 0 else 0

    def predict(self, inputs):
        # Вычисляем взвешенную сумму: w1*x1 + w2*x2 + bias
        total = np.dot(self.weights, inputs) + self.bias
        return self.activation(total)

    def train(self, X, y):
        # Цикл обучения
        for epoch in range(self.epochs):
            for inputs, target in zip(X, y):
                prediction = self.predict(inputs)
                error = target - prediction  # ошибка = цель - предсказание
                
                # Обновляем веса и смещение по правилу перцептрона
                self.weights += self.lr * error * inputs
                self.bias += self.lr * error

        print(f"Обучение завершено за {self.epochs} эпох.")

def main():
    # 1. Создание набора данных для логической функции AND
    X = np.array([[0, 0],
                  [0, 1],
                  [1, 0],
                  [1, 1]])
    
    # Целевые значения для AND
    y_and = np.array([0, 0, 0, 1])
    
    # Можно также обучить на OR, заменив y_and на:
    # y_or = np.array([0, 1, 1, 1])
    
    # 2. Инициализация перцептрона
    perceptron = Perceptron(input_size=2, learning_rate=0.1, epochs=20)
    
    print("Начальные веса:", perceptron.weights)
    print("Начальное смещение:", perceptron.bias)
    
    # 3. Обучение
    perceptron.train(X, y_and)
    
    # 4. Тестирование и вывод результатов
    print("\nФинальные веса:", perceptron.weights)
    print("Финальное смещение:", perceptron.bias)
    
    print("\nТестирование на данных:")
    print("Вход\t\tОжидаемый выход\t\tПредсказание")
    for inputs, target in zip(X, y_and):
        prediction = perceptron.predict(inputs)
        print(f"{inputs}\t\t{target}\t\t\t{prediction}")

if __name__ == "__main__":
    main()