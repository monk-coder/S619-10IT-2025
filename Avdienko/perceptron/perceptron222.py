import numpy as np


class Perceptron:
    """Однослойный перцептрон для бинарной классификации"""

    def __init__(self, num_inputs=2, learning_rate=0.1):
        """
        Инициализация перцептрона

        Args:
            num_inputs: количество входных признаков
            learning_rate: коэффициент обучения
        """
        # Инициализация весов небольшими случайными значениями
        self.weights = np.random.randn(num_inputs) * 0.1
        self.bias = np.random.randn() * 0.1
        self.learning_rate = learning_rate

    def activate(self, weighted_sum):
        """
        Ступенчатая функция активации

        Args:
            weighted_sum: взвешенная сумма

        Returns:
            1 если weighted_sum >= 0, иначе 0
        """
        return 1 if weighted_sum >= 0 else 0

    def predict(self, inputs):
        """
        Предсказание выхода для заданных входов

        Args:
            inputs: входные значения

        Returns:
            Предсказанный класс (0 или 1)
        """
        # Вычисление взвешенной суммы: w1*x1 + w2*x2 + b
        weighted_sum = np.dot(self.weights, inputs) + self.bias
        return self.activate(weighted_sum)

    def train(self, training_data, targets, epochs=20):
        """
        Обучение перцептрона

        Args:
            training_data: обучающие данные
            targets: целевые значения
            epochs: количество эпох обучения
        """
        print("Начало обучения перцептрона...")
        print(f"Начальные веса: {self.weights}, смещение: {self.bias:.4f}")
        print("-" * 50)

        for epoch in range(epochs):
            total_error = 0

            # Проход по всем обучающим примерам
            for inputs, target in zip(training_data, targets):
                # Предсказание выхода
                prediction = self.predict(inputs)

                # Вычисление ошибки
                error = target - prediction
                total_error += abs(error)

                # Обновление весов и смещения
                self.weights += self.learning_rate * error * inputs
                self.bias += self.learning_rate * error

            # Вывод информации о текущей эпохе
            if (epoch + 1) % 5 == 0 or epoch == 0:
                print(f"Эпоха {epoch + 1:2d}: ошибка = {total_error}")

            # Если ошибка равна 0, обучение завершено
            if total_error == 0:
                print(f"\nОбучение завершено на эпохе {epoch + 1}")
                break

        print("-" * 50)
        print(f"Финальные веса: {self.weights}, смещение: {self.bias:.4f}")

    def evaluate(self, test_data, targets):
        """
        Оценка точности обученного перцептрона

        Args:
            test_data: тестовые данные
            targets: целевые значения
        """
        print("\n" + "=" * 50)
        print("Тестирование обученного перцептрона")
        print("=" * 50)

        correct = 0
        total = len(test_data)

        for i, (inputs, target) in enumerate(zip(test_data, targets)):
            prediction = self.predict(inputs)
            status = "✓" if prediction == target else "✗"

            if prediction == target:
                correct += 1

            print(f"Вход: {inputs}, "
                  f"Ожидаемый: {target}, "
                  f"Предсказанный: {prediction} {status}")

        accuracy = (correct / total) * 100
        print(f"\nТочность: {correct}/{total} ({accuracy:.1f}%)")


def main():
    """Основная функция программы"""

    # 1. Создание набора данных для логической функции AND
    # AND: 1 только когда оба входа равны 1
    print("Логическая функция AND:")
    print("0 AND 0 = 0")
    print("0 AND 1 = 0")
    print("1 AND 0 = 0")
    print("1 AND 1 = 1")
    print()

    # Входные данные
    X = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])

    # Целевые значения для AND
    y = np.array([0, 0, 0, 1])

    # 2. Инициализация перцептрона
    perceptron = Perceptron(num_inputs=2, learning_rate=0.1)

    # 3. Обучение перцептрона
    perceptron.train(X, y, epochs=20)

    # 4. Тестирование перцептрона
    perceptron.evaluate(X, y)

    # Дополнительная демонстрация работы
    print("\n" + "=" * 50)
    print("Демонстрация работы на всех комбинациях:")
    print("=" * 50)

    for inputs in X:
        result = perceptron.predict(inputs)
        print(f"{inputs[0]} AND {inputs[1]} = {result}")


if __name__ == "__main__":
    main()