"""
perceptron.py
Однослойный перцептрон для реализации логической функции AND
"""

import numpy as np


class Perceptron:
    """Однослойный перцептрон для бинарной классификации"""

    def __init__(self, input_size: int, learning_rate: float = 0.1):
        """
        Инициализация перцептрона

        Args:
            input_size: количество входных признаков
            learning_rate: коэффициент обучения
        """
        # Инициализация весов случайными малыми значениями
        self.weights = np.random.randn(input_size) * 0.1
        self.bias = np.random.randn() * 0.1
        self.learning_rate = learning_rate

    @staticmethod
    def activation(weighted_sum: float) -> int:
        """
        Ступенчатая функция активации

        Args:
            weighted_sum: взвешенная сумма входов

        Returns:
            1 если weighted_sum >= 0, иначе 0
        """
        return 1 if weighted_sum >= 0 else 0

    def predict(self, inputs: np.ndarray) -> int:
        """
        Предсказание выходного значения

        Args:
            inputs: входной вектор

        Returns:
            Предсказание (0 или 1)
        """
        # Вычисление взвешенной суммы
        weighted_sum = np.dot(inputs, self.weights) + self.bias
        # Применение функции активации
        return self.activation(weighted_sum)

    def train(self, training_inputs: np.ndarray, labels: np.ndarray, epochs: int = 20):
        """
        Обучение перцептрона

        Args:
            training_inputs: обучающие примеры
            labels: целевые значения
            epochs: количество эпох обучения
        """
        print("Начало обучения перцептрона...")
        print(f"Исходные веса: {self.weights}, смещение: {self.bias:.4f}\n")

        for epoch in range(epochs):
            total_error = 0

            for inputs, label in zip(training_inputs, labels):
                # Предсказание для текущего примера
                prediction = self.predict(inputs)

                # Вычисление ошибки
                error = label - prediction
                total_error += abs(error)

                # Обновление весов по правилу обучения перцептрона
                self.weights += self.learning_rate * error * inputs
                self.bias += self.learning_rate * error

            # Вывод информации о текущей эпохе
            print(f"Эпоха {epoch + 1}/{epochs}, "
                  f"Суммарная ошибка: {total_error}, "
                  f"Веса: {self.weights}, "
                  f"Смещение: {self.bias:.4f}")

            # Если ошибка равна 0, обучение можно прекратить
            if total_error == 0:
                print(f"\nОбучение завершено досрочно на эпохе {epoch + 1}")
                break

    def evaluate(self, test_inputs: np.ndarray, test_labels: np.ndarray):
        """
        Оценка точности перцептрона

        Args:
            test_inputs: тестовые примеры
            test_labels: целевые значения
        """
        print("\n" + "=" * 50)
        print("ТЕСТИРОВАНИЕ")
        print("=" * 50)

        correct = 0
        total = len(test_inputs)

        for inputs, label in zip(test_inputs, test_labels):
            prediction = self.predict(inputs)
            is_correct = prediction == label
            if is_correct:
                correct += 1

            print(f"Вход: {inputs} -> "
                  f"Ожидалось: {label}, "
                  f"Предсказано: {prediction} "
                  f"{'✓' if is_correct else '✗'}")

        accuracy = (correct / total) * 100
        print(f"\nТочность: {correct}/{total} ({accuracy:.1f}%)")


def main():
    """Основная функция программы"""
    print("=" * 50)
    print("ОБУЧЕНИЕ ПЕРСЕПТРОНА ДЛЯ ЛОГИЧЕСКОЙ ФУНКЦИИ AND")
    print("=" * 50)

    # 1. Создание набора данных для логической функции AND
    # AND: 0 & 0 = 0, 0 & 1 = 0, 1 & 0 = 0, 1 & 1 = 1
    training_inputs = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])

    labels = np.array([0, 0, 0, 1])

    # 2. Инициализация перцептрона
    # У нас 2 входа, поэтому input_size = 2
    perceptron = Perceptron(input_size=2, learning_rate=0.1)

    # 3. Обучение перцептрона
    perceptron.train(training_inputs, labels, epochs=20)

    # 4. Тестирование обученного перцептрона
    perceptron.evaluate(training_inputs, labels)

    # 5. Вывод финальных параметров
    print("\n" + "=" * 50)
    print("ФИНАЛЬНЫЕ ПАРАМЕТРЫ ПЕРСЕПТРОНА")
    print("=" * 50)
    print(f"Веса: {perceptron.weights}")
    print(f"Смещение: {perceptron.bias:.4f}")

    # 6. Демонстрация работы на новых данных
    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ")
    print("=" * 50)

    test_cases = [
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1],
        [0.5, 0.5],  # Промежуточные значения
        [0.8, 0.2]
    ]

    for test_input in test_cases:
        inputs_array = np.array(test_input)
        prediction = perceptron.predict(inputs_array)
        print(f"Вход: {test_input} -> Предсказание: {prediction}")


if __name__ == "__main__":
    main()