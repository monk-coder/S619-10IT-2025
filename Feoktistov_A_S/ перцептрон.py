import numpy as np

class Perceptron:
    def __init__(self, input_size, learning_rate=0.1, epochs=100):
        """
        Инициализация перцептрона
        
        Args:
            input_size: количество входных признаков
            learning_rate: скорость обучения
            epochs: количество эпох обучения
        """
        self.weights = np.random.randn(input_size + 1)  # +1 для смещения (bias)
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.losses = []
    
    def activation_function(self, x):
        return 1 if x >= 0 else 0
    
    def predict(self, inputs):
        """
        Args:
            inputs: входные данные (массив длиной input_size)
        
        Returns:
            Предсказанный класс (0 или 1)
        """
        # Добавляем смещение (bias = 1)
        inputs_with_bias = np.insert(inputs, 0, 1)
        # Вычисляем взвешенную сумму
        weighted_sum = np.dot(self.weights, inputs_with_bias)
        # Применяем функцию активации
        return self.activation_function(weighted_sum)
    
    def train(self, X_train, y_train):
        for epoch in range(self.epochs):
            total_error = 0
            
            for inputs, target in zip(X_train, y_train):
                # Предсказание
                prediction = self.predict(inputs)
                # Вычисление ошибки
                error = target - prediction
                total_error += abs(error)
                
                # Обновление весов
                if error != 0:
                    # Добавляем смещение к входным данным
                    inputs_with_bias = np.insert(inputs, 0, 1)
                    # Обновляем веса по правилу перцептрона
                    self.weights += self.learning_rate * error * inputs_with_bias
            
            # Сохраняем среднюю ошибку для этой эпохи
            self.losses.append(total_error / len(X_train))
            
            # Вывод прогресса обучения
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Эпоха {epoch + 1}/{self.epochs}, Средняя ошибка: {self.losses[-1]:.4f}")
            
            # Остановка, если модель уже обучилась
            if self.losses[-1] == 0:
                print(f"Обучение завершено на эпохе {epoch + 1}")
                break
    
    def evaluate(self, X_test, y_test):
        correct = 0
        for inputs, target in zip(X_test, y_test):
            prediction = self.predict(inputs)
            if prediction == target:
                correct += 1
        
        accuracy = correct / len(X_test) * 100
        print(f"Точность: {accuracy:.2f}%")
        return accuracy

def create_and_dataset():
    X = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])
    y = np.array([0, 0, 0, 1])  # AND: только [1,1] дает 1
    return X, y

def create_or_dataset():
    """Создает набор данных для функции OR"""
    X = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])
    y = np.array([0, 1, 1, 1])  # OR: только [0,0] дает 0
    return X, y


def main():
    # Выбор функции (AND или OR)
    function_type = "AND"  # Измените на "OR" для другой функции
    
    # Создание набора данных
    if function_type == "AND":
        X, y = create_and_dataset()
        print("Обучение на функции AND:")
    else:
        X, y = create_or_dataset()
        print("Обучение на функции OR:")

    print("Обучающие данные:")
    for i in range(len(X)):
        print(f"  Вход: {X[i]}, Цель: {y[i]}")
    print()
    
    perceptron = Perceptron(input_size=2, learning_rate=0.1, epochs=50)
    perceptron.train(X, y)
    
    # Оценка на обучающих данных
    print(f"\nРезультаты для функции {function_type}:")
    perceptron.evaluate(X, y)

    print("\nПредсказания модели:")
    test_cases = [[0, 0], [0, 1], [1, 0], [1, 1]]
    for inputs in test_cases:
        prediction = perceptron.predict(inputs)
        print(f"  Вход: {inputs} -> Предсказание: {prediction}")
    
    print(f"\nОбученные веса:")
    print(f"  Вес смещения (w0): {perceptron.weights[0]:.4f}")
    print(f"  Вес для x1 (w1): {perceptron.weights[1]:.4f}")
    print(f"  Вес для x2 (w2): {perceptron.weights[2]:.4f}")
    
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(range(1, len(perceptron.losses) + 1), perceptron.losses, marker='o')
        plt.xlabel('Эпоха')
        plt.ylabel('Средняя ошибка')
        plt.title('Процесс обучения')
        plt.grid(True)

        plt.subplot(1, 2, 2)
        
        # x2 = -(w0 + w1*x1)/w2
        x1 = np.array([-0.5, 1.5])
        if perceptron.weights[2] != 0:
            x2 = -(perceptron.weights[0] + perceptron.weights[1] * x1) / perceptron.weights[2]
            plt.plot(x1, x2, 'r-', label='Разделяющая линия')
        

        colors = ['blue' if label == 0 else 'green' for label in y]
        for i, (point, color) in enumerate(zip(X, colors)):
            plt.scatter(point[0], point[1], c=color, s=100, 
                       marker='o' if y[i] == 0 else 's', label=f'Класс {y[i]}' if i == 0 else "")
        
        plt.xlim(-0.5, 1.5)
        plt.ylim(-0.5, 1.5)
        plt.xlabel('x1')
        plt.ylabel('x2')
        plt.title('Разделяющая линия')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("\nДля визуализации установите matplotlib: pip install matplotlib")


if __name__ == "__main__":
    main()
